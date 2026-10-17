from pathlib import Path
import json
import shutil
import sqlite3
import tempfile
import unittest
import numpy as np
from fastapi.testclient import TestClient
from continuityguard.features import matrix
from continuityguard.simulation import Experiment, SERVICES, simulate, service_breaches
from continuityguard.evaluation import alert_times
from continuityguard.runtime import Engine, Journal
from continuityguard.models import ModelBundle
from continuityguard.web import create_app

ARTIFACTS=Path(__file__).resolve().parents[1]/'artifacts'

class CausalDataTests(unittest.TestCase):
    def test_future_changes_cannot_change_past_features(self):
        events,_=simulate(Experiment('pool_exhaustion',91))
        changed=[dict(e) for e in events]
        for event in changed[160*4:]:
            event['queue_depth']+=500
            event['latency_p95_ms']*=4
        before,_=matrix(events)
        after,_=matrix(changed)
        np.testing.assert_array_equal(before[:160*4],after[:160*4])

    def test_pair_has_identical_pre_action_history_and_demand(self):
        spec=Experiment('pool_exhaustion',92)
        a,_=simulate(spec)
        b,_=simulate(spec,action='defer_batch',action_at=140)
        self.assertEqual(a[:140*4],b[:140*4])
        self.assertEqual([e['requests'] for e in a if e['service']=='urgent-results'],[e['requests'] for e in b if e['service']=='urgent-results'])

    def test_breach_requires_three_windows(self):
        events,_=simulate(Experiment('healthy',93))
        for event in events[:2*4]:
            event['latency_p95_ms']=2000
        self.assertFalse(any(b.any() for b in service_breaches(events).values()))

    def test_persistence_does_not_invent_an_early_alert(self):
        flags=np.zeros(80,dtype=bool)
        flags[4*8:]=True
        alerts=alert_times(flags,np.ones(80,dtype=bool))
        self.assertEqual(alerts['database'],[10])

    def test_split_seeds_are_disjoint(self):
        manifest=json.loads((ARTIFACTS/'split-manifest.json').read_text())
        used=set()
        for runs in manifest.values():
            seeds={r['seed'] for r in runs}
            self.assertEqual(len(seeds),len(runs))
            self.assertFalse(used & seeds)
            used |= seeds

class IntegrityTests(unittest.TestCase):
    def test_model_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            shutil.copy(ARTIFACTS/'manifest.json',folder)
            (folder/'models.joblib').write_bytes((ARTIFACTS/'models.joblib').read_bytes()+b'changed')
            with self.assertRaisesRegex(RuntimeError,'integrity'):
                ModelBundle(folder)

    def test_audit_modification_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            journal=Journal(str(Path(folder)/'audit.sqlite'))
            journal.append('test',{'measured':1})
            self.assertTrue(journal.verify()['valid'])
            journal.db.execute("UPDATE audit SET body='tampered' WHERE id=1")
            journal.db.commit()
            self.assertFalse(journal.verify()['valid'])
            journal.close()

class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.engine=Engine(ARTIFACTS)
        self.events,_=simulate(Experiment('pool_exhaustion',94))

    def tearDown(self):
        self.engine.close()

    def test_duplicates_do_not_advance_feature_state(self):
        self.engine.ingest(self.events[:4])
        self.engine.ingest(self.events[:4])
        state=self.engine.snapshot()
        self.assertEqual(state['accepted'],4)
        self.assertEqual(state['duplicates'],4)
        self.assertEqual(len(self.engine.window.history['database']),1)

    def test_out_of_order_event_is_rejected(self):
        self.engine.ingest(self.events[:8])
        older={**self.events[0],'event_id':'new-but-old-time'}
        self.engine.ingest([older])
        self.assertEqual(self.engine.rejected,1)

    def test_model_failure_is_explicit_and_falls_back(self):
        self.engine.bundle.predict=lambda x: (_ for _ in ()).throw(RuntimeError('unavailable'))
        self.engine.ingest(self.events[:4])
        self.assertIn('degraded',self.engine.snapshot()['model_status'])
        self.assertIsNone(self.engine.snapshot()['services'][0]['forecast_risk'])

    def test_missing_receipts_are_stale(self):
        self.assertTrue(self.engine.snapshot()['stale'])
        self.engine.ingest(self.events[:4])
        self.assertFalse(self.engine.snapshot()['stale'])
        self.engine.last_received-=10
        self.assertTrue(self.engine.snapshot()['stale'])

    def test_online_and_offline_model_inputs_match(self):
        expected,_=matrix(self.events[:80])
        captured=[]
        original=self.engine.bundle.predict
        def record(x):
            captured.extend(x.copy())
            return original(x)
        self.engine.bundle.predict=record
        for i in range(0,80,4):
            self.engine.ingest(self.events[i:i+4])
        np.testing.assert_array_equal(np.asarray(captured),expected)

    def test_event_gap_resets_warmup_and_persistence(self):
        from datetime import datetime,timedelta
        self.engine.ingest(self.events[:80])
        event=dict(self.events[80])
        event['event_time']=(datetime.fromisoformat(event['event_time'])+timedelta(minutes=10)).isoformat()
        self.engine.ingest([event])
        self.assertFalse(self.engine.services['database']['warm'])
        self.assertEqual(len(self.engine.votes['database']),1)
        self.assertEqual(len(self.engine.slo['database']),1)

    def test_nonfinite_input_does_not_poison_next_valid_event(self):
        invalid={**self.events[0],'latency_p95_ms':float('nan')}
        self.engine.ingest([invalid])
        self.engine.ingest(self.events[:4])
        self.assertEqual(self.engine.accepted,4)
        self.assertEqual(self.engine.rejected,1)

    def test_nonfinite_model_output_uses_explicit_fallback(self):
        self.engine.bundle.predict=lambda x:(np.full(len(x),np.nan),np.ones(len(x)),np.ones(len(x)))
        self.engine.ingest(self.events[:4])
        self.assertIn('degraded',self.engine.model_status)

    def test_online_incident_times_match_offline_policy(self):
        from continuityguard.features import timestamp
        x,ready=matrix(self.events)
        p,n,_=self.engine.bundle.predict(x)
        expected=alert_times(self.engine.bundle.decision_flags(p,n,x),ready)
        observed={s:[] for s in SERVICES}
        start=timestamp(self.events[0]['event_time'])
        for k in range(0,len(self.events),4):
            for incident in self.engine.ingest(self.events[k:k+4]):
                observed[incident['service']].append(int(timestamp(incident['event_time'])-start))
        self.assertEqual(observed,expected)

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        (root/'artifacts').symlink_to(ARTIFACTS,target_is_directory=True)
        token=root/'private-token'
        token.write_text('test-token-for-isolated-correctness-only')
        self.client=TestClient(create_app(root,token,auto_start=False))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None,None,None)
        self.temp.cleanup()

    def auth(self):
        result=self.client.post('/api/login',json={'token':'test-token-for-isolated-correctness-only'},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(result.status_code,200)

    def test_private_state_requires_authentication(self):
        self.assertEqual(self.client.get('/api/state').status_code,401)
        self.assertEqual(self.client.get('/api/platform-proof').status_code,401)

    def test_platform_proof_matches_loaded_model(self):
        self.auth()
        proof=self.client.get('/api/platform-proof').json()
        self.assertEqual(proof['architecture'],'s390x')
        self.assertEqual(proof['model']['sha256'],self.client.app.state.service.engine.bundle.manifest['sha256'])

    def test_mutations_reject_cross_origin(self):
        self.auth()
        result=self.client.post('/api/pause',json={},headers={'X-ContinuityGuard':'operator','Origin':'https://untrusted.example'})
        self.assertEqual(result.status_code,403)

    def test_nonfinite_telemetry_is_rejected(self):
        self.auth()
        events,_=simulate(Experiment('healthy',95))
        event={**events[0],'latency_p95_ms':'NaN'}
        result=self.client.post('/api/events',json={'events':[event]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(result.status_code,422)

    def test_ingestion_is_validated_and_queued(self):
        self.auth()
        events,_=simulate(Experiment('healthy',96))
        result=self.client.post('/api/events',json={'events':events[:4]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(result.status_code,202)
        self.assertEqual(result.json()['accepted_into_queue'],4)

    def test_excessive_batch_is_rejected(self):
        self.auth()
        events,_=simulate(Experiment('healthy',97))
        result=self.client.post('/api/events',json={'events':events[:132]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(result.status_code,422)

    def test_control_actions_do_not_accept_shell_commands(self):
        self.auth()
        result=self.client.post('/api/scenario',json={'name':'rm -rf /','seed':1,'speed':4},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(result.status_code,422)

    def test_saturated_queue_returns_explicit_backpressure(self):
        import asyncio
        self.auth()
        service=self.client.app.state.service
        async def saturate():
            service.consumer.cancel()
            try:
                await service.consumer
            except asyncio.CancelledError:
                pass
            for _ in range(service.queue.maxsize):
                service.queue.put_nowait((service.generation,[]))
        self.client.portal.call(saturate)
        events,_=simulate(Experiment('healthy',98))
        try:
            result=self.client.post('/api/events',json={'events':events[:4]},headers={'X-ContinuityGuard':'operator'})
            self.assertEqual(result.status_code,429)
            self.assertEqual(service.rejected_batches,1)
        finally:
            async def drain():
                while not service.queue.empty():
                    service.queue.get_nowait()
                    service.queue.task_done()
            self.client.portal.call(drain)

    def test_event_journal_survives_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'journal.sqlite')
            journal=Journal(path)
            journal.append('persistence_test',{'value':3})
            journal.close()
            reopened=Journal(path)
            self.assertEqual(reopened.verify()['records'],1)
            self.assertTrue(reopened.verify()['valid'])
            reopened.close()

    def test_unicode_login_is_rejected_without_server_error(self):
        response=self.client.post('/api/login',json={'token':'é'*32},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(response.status_code,401)

    def test_actual_chunked_body_limit_is_enforced(self):
        self.auth()
        response=self.client.post('/api/events',content=iter([b' '*600000,b' '*600000]),headers={'X-ContinuityGuard':'operator','Content-Type':'application/json'})
        self.assertEqual(response.status_code,413)

    def test_missing_operator_header_rejects_mutation(self):
        self.auth()
        self.assertEqual(self.client.post('/api/external-session').status_code,403)

    def test_naive_timestamp_is_rejected(self):
        self.auth()
        events,_=simulate(Experiment('healthy',95))
        events[0]['event_time']='2026-10-17T00:00:00'
        r=self.client.post('/api/events',json={'events':events[:1]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(r.status_code,422)

    def test_impossible_failure_count_is_rejected(self):
        self.auth()
        events,_=simulate(Experiment('healthy',95))
        events[0]['failures']=events[0]['requests']+1
        r=self.client.post('/api/events',json={'events':events[:1]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(r.status_code,422)

    def test_fractional_request_count_is_rejected(self):
        self.auth()
        events,_=simulate(Experiment('healthy',95))
        events[0]['requests']=12.5
        r=self.client.post('/api/events',json={'events':events[:1]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(r.status_code,422)

    def test_external_events_cannot_impersonate_sandbox_provenance(self):
        self.auth()
        events,_=simulate(Experiment('healthy',95))
        r=self.client.post('/api/events',json={'events':events[:4]},headers={'X-ContinuityGuard':'operator'})
        self.assertEqual(r.status_code,202)
        self.client.portal.call(self.client.app.state.service.queue.join)
        self.assertTrue(all(e['source_mode']=='external' for e in self.client.get('/api/state').json()['services']))

    def test_sandbox_rejects_external_input_until_explicit_transition(self):
        self.auth()
        h={'X-ContinuityGuard':'operator'}
        self.assertEqual(self.client.post('/api/scenario',json={'name':'healthy','seed':1,'speed':4},headers=h).status_code,200)
        events,_=simulate(Experiment('healthy',95))
        self.assertEqual(self.client.post('/api/events',json={'events':events[:4]},headers=h).status_code,409)
        self.assertEqual(self.client.post('/api/external-session',json={},headers=h).status_code,200)
        self.assertEqual(self.client.get('/api/state').json()['accepted'],0)
        self.assertEqual(self.client.get('/api/state').json()['mode'],'external')

    def test_pause_without_active_replay_is_rejected(self):
        self.auth()
        self.assertEqual(self.client.post('/api/pause',json={},headers={'X-ContinuityGuard':'operator'}).status_code,409)

    def test_consumer_failure_is_visible_and_does_not_deadlock_queue(self):
        self.auth()
        service=self.client.app.state.service
        service.engine.ingest=lambda events: (_ for _ in ()).throw(OSError('simulated storage failure'))
        events,_=simulate(Experiment('healthy',95))
        self.client.post('/api/events',json={'events':events[:4]},headers={'X-ContinuityGuard':'operator'})
        self.client.portal.call(service.queue.join)
        self.assertEqual(service.failed_batches,1)
        self.assertEqual(self.client.get('/api/health').status_code,503)

class ExplanationTests(unittest.TestCase):
    def test_unavailable_model_returns_grounded_labeled_fallback(self):
        from continuityguard.explain import Explainer
        from continuityguard.models import RUNBOOKS
        journal=Journal(':memory:')
        explainer=Explainer('/deliberately-missing-model.gguf',journal)
        incident={'id':'test','service':'database','runbook':RUNBOOKS['pool'],'evidence':[{'id':'E1','label':'Connection pool occupancy','value':91,'unit':'%'}]}
        explainer.request(incident)
        explainer.close()
        result=explainer.status('test')
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['mode'],'deterministic fallback')
        self.assertEqual(result['evidence_ids'],['E1'])
        self.assertIn('91',result['summary'])
        journal.close()

if __name__=='__main__':
    unittest.main()
