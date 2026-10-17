"""V5: validation-selected repeat filtering with a shared bounded alert lifecycle.

Training/selection and final evaluation are separate callable notebook cells.
The model and protocol are frozen before any fresh final run is generated.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.metadata,json,time
import joblib
import numpy as np
from scipy.special import logit
from sklearn.ensemble import HistGradientBoostingClassifier,IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score,brier_score_loss
from .train import dataset,stack,calibrated,raw_probability,run_bootstrap,write_plots
from .evaluation import evaluate_runs,objective,static_flags,confirmed_flags,robust_score,alert_times,repeat_refresh_flags
from .simulation import Experiment,SERVICES,HORIZON,paired_response
from .models import ModelBundle,diagnosis
from .features import FEATURE_NAMES

PROTOCOL={
 'version':'cg-2026-10-17-v5',
 'splits':{'train':[300000,40],'calibration':[310000,10],'validation':[320000,20],'test':[500000,30],'stress':[520000,12]},
 'trend_guards':[False,True],
 'warning_gates':[0,.05,.1,.2,.35,.5,.65,.8,.9,.97],
 'selection':'Prefer validation precision and early recall both >= corrected static baseline; maximize 0.65 early recall + 0.35 precision with healthy false-alarm penalty; report if no strict improvement.',
 'alert_lifecycle':'Every detector uses 3-of-5 persistence, 30-second cooldown and a 60-second persistent-episode recheck. No past alert can suppress notifications forever.',
 'matching':'Unchanged: one alert per incident, from 60 seconds before onset through 15 seconds after incident end.',
 'risk_policy':'Initial static warnings are retained. Only persistent repeat notifications may be suppressed by low learned risk. Observed breach limits always permit a repeat. Validation selects whether rising trends also bypass filtering. Independent forecast paging is disabled.',
 'history':'v1/v2/v3/v4 tests were inspected development history. V4 initial-warning filtering traded recall for precision and was rejected for deployment. V5 preserves first warnings; its fresh final seeds are generated only after freezing model/policy hashes.',
}

def dump(path,value):path.write_text(json.dumps(value,indent=2))

def flags(probability,run,threshold,gate):
 return (probability>=threshold)|(static_flags(run['x'])&(probability>=gate))|confirmed_flags(run['x'])

def fit_select(output):
 out=Path(output);out.mkdir(parents=True,exist_ok=True)
 dump(out/'protocol.json',{**PROTOCOL,'declared_utc':datetime.now(timezone.utc).isoformat()})
 started=time.perf_counter()
 print('Generating training, calibration and validation only; final test not generated.',flush=True)
 runs={k:dataset(*PROTOCOL['splits'][k]) for k in ('train','calibration','validation')}
 train,calibration,validation=(runs[k] for k in ('train','calibration','validation'))
 x,y=stack(train);xc,yc=stack(calibration);xv,yv=stack(validation)
 normal=np.concatenate([r['x'][r['ready']] for r in train if r['manifest']['scenario'].startswith('healthy')])
 novelty=IsolationForest(n_estimators=100,max_samples=256,random_state=17,n_jobs=1).fit(normal)
 normal_reference=np.sort(-novelty.score_samples(np.concatenate([r['x'][r['ready']] for r in calibration if r['manifest']['scenario'].startswith('healthy')])))
 candidates={
  'logistic_C0.1':make_pipeline(StandardScaler(),LogisticRegression(C=.1,max_iter=500,random_state=17)),
  'logistic_C1':make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=500,random_state=17)),
  'boosted_trees_7_leaves':HistGradientBoostingClassifier(max_iter=180,max_leaf_nodes=7,learning_rate=.06,l2_regularization=1,early_stopping=False,random_state=17),
  'boosted_trees_15_leaves':HistGradientBoostingClassifier(max_iter=180,max_leaf_nodes=15,learning_rate=.06,l2_regularization=2,early_stopping=False,random_state=17),
  'boosted_trees_31_leaves':HistGradientBoostingClassifier(max_iter=180,max_leaf_nodes=31,learning_rate=.06,l2_regularization=3,early_stopping=False,random_state=17),
 }
 baseline=evaluate_runs(validation,[static_flags(r['x']) for r in validation],keep_details=False)
 selections=[];comparisons=[];fitted={}
 for name,model in candidates.items():
  then=time.perf_counter();print('Fit and validate',name,flush=True)
  model.fit(x,y)
  pc=np.clip(raw_probability(model,xc),1e-6,1-1e-6)
  calibrator=LogisticRegression(C=10,random_state=17).fit(logit(pc).reshape(-1,1),yc)
  pv=calibrated(model,calibrator,xv)
  comparisons.append({'name':name,'validation_pr_auc':float(average_precision_score(yv,pv)),'validation_brier':float(brier_score_loss(yv,pv)),'fit_seconds':round(time.perf_counter()-then,3)})
  fitted[name]=(model,calibrator)
  probabilities=[calibrated(model,calibrator,r['x']) for r in validation]
  for trend_guard in PROTOCOL['trend_guards']:
   for gate in PROTOCOL['warning_gates']:
    metrics=evaluate_runs(validation,[static_flags(r['x']) for r in validation],keep_details=False,refresh_by_run=[repeat_refresh_flags(p,r['x'],gate,trend_guard) for p,r in zip(probabilities,validation)])
    feasible=metrics['early_warning_recall']>=baseline['early_warning_recall'] and metrics['incident_precision']>=baseline['incident_precision']
    selections.append({'candidate':name,'forecast_threshold':1.01,'warning_gate':gate,'trend_guard':trend_guard,'feasible_vs_static':feasible,'objective':objective(metrics),'metrics':metrics})
  best=max((r for r in selections if r['candidate']==name),key=lambda r:(r['feasible_vs_static'],r['objective'],r['metrics']['incident_precision']))
  print(json.dumps({'candidate':name,'best_validation':{k:best[k] for k in ('forecast_threshold','warning_gate','feasible_vs_static','objective')},'precision':best['metrics']['incident_precision'],'early_recall':best['metrics']['early_warning_recall']}),flush=True)
 selected=max(selections,key=lambda r:(r['feasible_vs_static'],r['objective'],r['metrics']['incident_precision'],-r['metrics']['alerts']))
 model,calibrator=fitted[selected['candidate']]
 center=np.median(normal[:,:7],axis=0);scale=np.maximum(1.4826*np.median(np.abs(normal[:,:7]-center),axis=0),.003)
 robust_options=[(objective(evaluate_runs(validation,[robust_score(r['x'],center,scale)>t for r in validation],keep_details=False)),t) for t in (5.,7.,9.,12.,16.)]
 policy={'mode':'repeat_filtered','forecast_threshold':1.01,'standalone_forecast_paging':False,'warning_gate':selected['warning_gate'],'trend_guard':selected['trend_guard'],'novelty_threshold':float(np.quantile(normal_reference,.995)),'novelty_quantile':.995,'refresh_seconds':60}
 state={'feature_names':list(FEATURE_NAMES),'forecast':model,'calibrator':calibrator,'novelty':novelty,'normal_novelty':normal_reference,'policy':policy,'robust_center':center,'robust_scale':scale,'robust_threshold':max(robust_options)[1]}
 joblib.dump(state,out/'models.joblib',compress=3)
 manifest={'version':PROTOCOL['version'],'trained_utc':datetime.now(timezone.utc).isoformat(),'architecture':__import__('platform').machine(),'model':selected['candidate'],'forecast_horizon_seconds':HORIZON,'feature_count':len(state['feature_names']),'sha256':hashlib.sha256((out/'models.joblib').read_bytes()).hexdigest(),'packages':{p:importlib.metadata.version(p) for p in ('numpy','scikit-learn','scipy','joblib')}}
 dump(out/'manifest.json',manifest)
 dump(out/'validation-selection.json',{'static_baseline':baseline,'selected':selected,'candidate_models':comparisons,'all_options':selections,'forecast_training_rows':len(y),'fit_select_seconds':round(time.perf_counter()-started,3)})
 dump(out/'split-manifest.json',{name:[r['manifest'] for r in rs] for name,rs in runs.items()})
 dump(out/'freeze.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'model_sha256':manifest['sha256'],'policy':policy,'test_not_generated_during_selection':True,'protocol_sha256':hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest()})
 print('FROZEN before final evaluation:',json.dumps(manifest),flush=True)
 return selected

def evaluate_frozen(output):
 out=Path(output);freeze=json.loads((out/'freeze.json').read_text())
 assert hashlib.sha256((out/'models.joblib').read_bytes()).hexdigest()==freeze['model_sha256']
 assert hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest()==freeze['protocol_sha256']
 bundle=ModelBundle(out);selection=json.loads((out/'validation-selection.json').read_text())
 print('Generating predeclared fresh final and stress runs AFTER freeze.',flush=True)
 test=dataset(*PROTOCOL['splits']['test']);unseen=dataset(*PROTOCOL['splits']['stress'],kinds=('abrupt_failure',))
 predictions=[bundle.predict(r['x']) for r in test]
 probabilities=[p for p,_,_ in predictions];novelty=[n for _,n,_ in predictions]
 policy=bundle.state['policy'];state=bundle.state
 all_flags={
 'Static thresholds':[static_flags(r['x']) for r in test],
 'Robust statistics':[robust_score(r['x'],state['robust_center'],state['robust_scale'])>state['robust_threshold'] for r in test],
 'Isolation Forest':[n>policy['novelty_threshold'] for n in novelty],
 'ContinuityGuard':[bundle.decision_flags(p,n,r['x']) for (p,n,_),r in zip(predictions,test)]}
 refresh=[bundle.refresh_flags(p,r['x']) for p,r in zip(probabilities,test)]
 systems={name:evaluate_runs(test,fs,refresh_by_run=refresh if name=='ContinuityGuard' else None) for name,fs in all_flags.items()}
 xt,yt=stack(test);pt=calibrated(state['forecast'],state['calibrator'],xt)
 reliability=[]
 for low,high in zip(np.arange(0,1,.2),np.arange(.2,1.01,.2)):
  mask=(pt>=low)&(pt<high)
  reliability.append({'lower':float(low),'upper':float(high),'count':int(mask.sum()),'mean_prediction':float(pt[mask].mean()) if mask.any() else None,'observed_rate':float(yt[mask].mean()) if mask.any() else None})
 stress_flags=[];stress_refresh=[]
 for r in unseen:
  p,n,_=bundle.predict(r['x']);stress_flags.append(bundle.decision_flags(p,n,r['x']));stress_refresh.append(bundle.refresh_flags(p,r['x']))
 responses=[]
 for r,fs,allowed in zip(test,all_flags['ContinuityGuard'],refresh):
  pairs=[(t,s) for s,ts in alert_times(fs,r['ready'],allowed).items() for t in ts]
  if pairs and r['manifest']['scenario'] in {'pool_exhaustion','retry_storm'}:
   t,s=min(pairs);_,book=diagnosis(r['events'][t*len(SERVICES)+SERVICES.index(s)])
   if book['action']!='none':responses.append(paired_response(Experiment(r['manifest']['scenario'],r['manifest']['seed']),t,book['action']))
 ablations={
  'No ML repeat filter':systems['Static thresholds'],
  'ML repeat filter without rising-trend bypass':evaluate_runs(test,all_flags['ContinuityGuard'],refresh_by_run=[repeat_refresh_flags(p,r['x'],policy['warning_gate'],False) for p,r in zip(probabilities,test)]),
 }
 per_run={name:[evaluate_runs([r],[f],keep_details=False,refresh_by_run=[refresh[i]] if name=='ContinuityGuard' else None) for i,(r,f) in enumerate(zip(test,fs))] for name,fs in all_flags.items() if name in ('Static thresholds','ContinuityGuard')}
 draws=np.random.default_rng(97531).integers(0,len(test),(500,len(test)))
 deltas=[]
 for draw in draws:
  values={name:{k:sum(rows[i][k] for i in draw) for k in ('incidents','early_detections','detected','alerts')} for name,rows in per_run.items()}
  a,b=values['ContinuityGuard'],values['Static thresholds']
  deltas.append([a['early_detections']/max(1,a['incidents'])-b['early_detections']/max(1,b['incidents']),a['detected']/max(1,a['alerts'])-b['detected']/max(1,b['alerts'])])
 paired={'unit':'whole run; paired detector differences; simulator-conditional','replicates':500,'early_recall_delta_95':np.percentile(np.asarray(deltas)[:,0],[2.5,97.5]).tolist(),'precision_delta_95':np.percentile(np.asarray(deltas)[:,1],[2.5,97.5]).tolist()}
 report={'scope':'Synthetic service-simulator evaluation on LinuxONE; not real hospital validation','split':{'training_runs':240,'calibration_runs':60,'validation_runs':120,'test_runs':len(test),'unseen_abrupt_runs':len(unseen),'no_shared_seeds':True,'seconds_per_run':300,'forecast_training_rows':selection['forecast_training_rows']},'manifest':bundle.manifest,'candidate_models':selection['candidate_models'],'selected_model':bundle.manifest['model'],'policy':policy,'validation_policy_metrics':selection['selected']['metrics'],'systems':systems,'forecast_test':{'pr_auc':float(average_precision_score(yt,pt)),'brier_score':float(brier_score_loss(yt,pt)),'positive_prevalence':float(yt.mean()),'reliability_bins':reliability},'run_bootstrap':run_bootstrap(test,systems),'paired_bootstrap':paired,'ablations':ablations,'unseen_abrupt_failures':evaluate_runs(unseen,stress_flags,refresh_by_run=stress_refresh),'paired_responses':responses,'method':{'slo':'p95 >1000 ms or failures/requests >0.10, sustained for three 1-second windows','persistence':PROTOCOL['alert_lifecycle'],'matching':'one alert per incident, from 60 seconds before onset through 15 seconds after incident end','selection':PROTOCOL['selection'],'development_history':PROTOCOL['history'],'novelty_is_probability':False},'limitations':['Synthetic simulator family, not hospital validation','Corrected scheduler applies equally; the learned filter acts only on repeats; prior results are historical','Initial threshold warnings are retained; repeat filtering can still delay follow-up notifications','Generation and intervention effects remain explicitly bounded','Fresh-run results do not establish cross-domain superiority'],'training_and_evaluation_seconds':selection['fit_select_seconds']}
 dump(out/'report.json',report)
 splits=json.loads((out/'split-manifest.json').read_text());splits.update(test=[r['manifest'] for r in test],stress=[r['manifest'] for r in unseen]);dump(out/'split-manifest.json',splits)
 dump(out/'test-execution.json',{'started_after_freeze':True,'freeze':freeze,'finished_utc':datetime.now(timezone.utc).isoformat(),'scope':'Reproduction of these same seeds later is not a new independent evaluation.'})
 write_plots(out,report,test,probabilities)
 print(json.dumps({name:{k:v for k,v in row.items() if k!='incident_details'} for name,row in systems.items()},indent=2),flush=True)
 print('Paired uncertainty:',json.dumps(paired),flush=True)
 return report

def main(output):
 fit_select(output)
 return evaluate_frozen(output)
