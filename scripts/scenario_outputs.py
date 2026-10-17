"""Reproducible scenario illustrations using the frozen submitted model.

These fixed-seed examples are illustrations, not an independent evaluation.
"""
from pathlib import Path
import json
import tempfile
from datetime import datetime
import numpy as np
from continuityguard.simulation import Experiment,SCENARIOS,SERVICES,simulate,service_breaches
from continuityguard.runtime import Engine

def main(root):
    root=Path(root);out=root/'artifacts/scenarios';out.mkdir(exist_ok=True)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    version=json.loads((root/'artifacts/manifest.json').read_text())['version']
    fig,axes=plt.subplots(4,2,figsize=(13,12));rows=[]
    for scenario,ax in zip(SCENARIOS,axes.flat):
        events,_=simulate(Experiment(scenario,101,strength=1.12))
        breaches=service_breaches(events);incidents=[]
        with tempfile.TemporaryDirectory() as folder:
            engine=Engine(root/'artifacts',str(Path(folder)/'scenario.sqlite'))
            for k in range(0,len(events),4):incidents.extend(engine.ingest(events[k:k+4]))
            engine.close()
        urgent=[e for e in events if e['service']=='urgent-results']
        base=datetime.fromisoformat(events[0]['event_time'])
        warning=[int((datetime.fromisoformat(i['event_time'])-base).total_seconds()) for i in incidents if i['service']=='urgent-results']
        times=np.flatnonzero(breaches['urgent-results']);first=int(times[0]) if len(times) else None
        row={'scenario':scenario,'seed':101,'strength':1.12,'all_service_alerts':len(incidents),'urgent_alert_seconds':warning,'first_urgent_sustained_breach_second':first,'scope':'Fixed-seed synthetic illustration, not new independent validation'};rows.append(row)
        ax.plot([e['latency_p95_ms'] for e in urgent],color='#167567',linewidth=1.5,label='Urgent-results latency')
        ax.axhline(1000,color='#be6d3f',linestyle='--',linewidth=1)
        for t in warning:ax.axvline(t,color='#315b83',alpha=.6)
        if first is not None:ax.axvline(first,color='#b44e48',linestyle=':',linewidth=2)
        ax.set(title=scenario.replace('_',' '),xlabel='Synthetic event seconds',ylabel='p95 latency (ms)');ax.grid(alpha=.15)
        if scenario=='pool_exhaustion':
            small,axis=plt.subplots(figsize=(10,4))
            axis.plot([e['latency_p95_ms'] for e in urgent],color='#167567',label='Urgent-results latency')
            axis.axhline(1000,color='#be6d3f',linestyle='--',label='Latency objective')
            for i,t in enumerate(warning):axis.axvline(t,color='#315b83',alpha=.7,label='Actual notification' if i==0 else None)
            if first is not None:axis.axvline(first,color='#b44e48',linestyle=':',label='Sustained breach onset')
            axis.set(title='Frozen '+version+' / controlled pool-pressure illustration',xlabel='Synthetic event seconds / seed 101, strength 1.12',ylabel='p95 latency (ms)');axis.grid(alpha=.15);axis.legend(fontsize=8)
            small.tight_layout();small.savefig(out/'pool-example.png',dpi=200);plt.close(small)
    axes.flat[-1].axis('off');axes.flat[-1].text(.02,.78,'All seven scenarios / '+version+'\n\nBlue: urgent-service notification\nRed dotted: first sustained breach\nOrange: latency objective only\n\nA breach can also follow error fraction.\nFixed seed 101; severity 1.12.\nThese illustrations do not replace final evaluation.',va='top',fontsize=12)
    fig.tight_layout();fig.savefig(out/'scenario-gallery.png',dpi=200);fig.savefig(out/'scenario-gallery.svg');plt.close(fig)
    svg=out/'scenario-gallery.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    (out/'outputs.json').write_text(json.dumps({'model_version':version,'scenarios':rows},indent=2));print(json.dumps(rows,indent=2))
    return rows

if __name__=='__main__':main(Path(__file__).resolve().parents[1])
