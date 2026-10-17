"""Bounded streaming state, incident policy, and a persistent audit journal."""
from collections import OrderedDict, deque
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sqlite3
import threading
import time
import uuid
import numpy as np
from .features import FeatureWindow, timestamp
from .models import ModelBundle, evidence, diagnosis
from .simulation import SERVICES, DEPENDENCIES, PRIORITIES
from .evaluation import static_flags

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

class Journal:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, received TEXT, service TEXT, body TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, body TEXT, previous TEXT, digest TEXT)')
        self.db.commit()
        self.lock = threading.RLock()

    def event(self, event):
        with self.lock:
            self.db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?)', (event['event_id'], now(), event['service'], canonical(event)))

    def commit(self):
        with self.lock:
            self.db.execute('DELETE FROM events WHERE rowid NOT IN (SELECT rowid FROM events ORDER BY rowid DESC LIMIT 5000)')
            self.db.commit()

    def append(self, kind, payload):
        with self.lock:
            previous = self.db.execute('SELECT digest FROM audit ORDER BY id DESC LIMIT 1').fetchone()
            previous = previous[0] if previous else '0'*64
            body = canonical({'time': now(), 'kind': kind, 'payload': payload})
            digest = hashlib.sha256((previous+body).encode()).hexdigest()
            self.db.execute('INSERT INTO audit (body,previous,digest) VALUES (?,?,?)', (body,previous,digest))
            self.db.commit()
            return digest

    def verify(self):
        with self.lock:
            rows = self.db.execute('SELECT body,previous,digest FROM audit ORDER BY id').fetchall()
        previous = '0'*64
        for body, linked, digest in rows:
            if linked != previous or hashlib.sha256((previous+body).encode()).hexdigest() != digest:
                return {'valid': False, 'records': len(rows), 'scope': 'local hash chain; not immutable or externally signed'}
            previous = digest
        return {'valid': True, 'records': len(rows), 'head': previous, 'scope': 'local hash chain; externally retain head to detect full-history replacement'}

    def close(self):
        self.db.close()

class Engine:
    def __init__(self, artifacts, database=':memory:'):
        self.bundle = ModelBundle(artifacts)
        self.journal = Journal(database)
        self.lock = threading.RLock()
        self.reset()
        self.journal.append('model_loaded', {'version': self.bundle.manifest['version'], 'sha256': self.bundle.manifest['sha256']})

    def reset(self):
        with self.lock:
            self.window = FeatureWindow()
            self.seen = OrderedDict()
            self.votes = {s: deque(maxlen=5) for s in SERVICES}
            self.slo = {s: deque(maxlen=3) for s in SERVICES}
            self.latched = {s: False for s in SERVICES}
            self.last_alert = {s: -float('inf') for s in SERVICES}
            self.services = {}
            self.incidents = deque(maxlen=100)
            self.chart = deque(maxlen=180)
            self.latencies = deque(maxlen=5000)
            self.accepted = self.duplicates = self.rejected = 0
            self.last_received = None
            self.model_status = 'ready'

    def ingest(self, events):
        started = time.perf_counter()
        with self.lock:
            accepted, rows, warm = [], [], []
            for event in events:
                if event['event_id'] in self.seen:
                    self.duplicates += 1
                    continue
                try:
                    row, ready = self.window.push(event)
                except (ValueError, KeyError):
                    self.rejected += 1
                    continue
                self.seen[event['event_id']] = True
                if len(self.seen) > 5000:
                    self.seen.popitem(last=False)
                accepted.append(event)
                rows.append(row)
                warm.append(ready)
            if not accepted:
                return []
            x = np.asarray(rows)
            try:
                probabilities, novelty, percentiles = self.bundle.predict(x)
                flags = self.bundle.decision_flags(probabilities, novelty, x)
                self.model_status = 'ready'
            except Exception:
                probabilities = percentiles = np.full(len(x), np.nan)
                flags = static_flags(x)
                self.model_status = 'degraded: static threshold fallback'
            created = []
            for i, event in enumerate(accepted):
                service = event['service']
                t = timestamp(event['event_time'])
                breach = event['latency_p95_ms'] > 1000 or event['failures']/event['requests'] > .10
                self.slo[service].append(breach)
                breached = len(self.slo[service]) == 3 and all(self.slo[service])
                probability = float(probabilities[i]) if np.isfinite(probabilities[i]) else None
                percentile = float(percentiles[i]) if np.isfinite(percentiles[i]) else None
                self.votes[service].append(bool(flags[i] and warm[i]))
                if not any(self.votes[service]):
                    self.latched[service] = False
                self.services[service] = {**event, 'forecast_risk': probability, 'novelty_percentile': percentile, 'warm': bool(warm[i]), 'breached': breached, 'flagged': bool(flags[i] and warm[i])}
                if sum(self.votes[service]) >= 3 and not self.latched[service] and t-self.last_alert[service] >= 30:
                    category, book = diagnosis(event)
                    affected = list(SERVICES[1:]) if service == 'database' else [service]
                    priority = sorted(affected, key=lambda s: PRIORITIES[s], reverse=True)
                    incident = {'id': uuid.uuid4().hex[:12], 'created_at': now(), 'event_time': event['event_time'], 'service': service, 'suspected_source': 'database dependency' if service != 'database' else 'database', 'category': category, 'risk': probability, 'novelty_percentile': percentile, 'already_breached': breached, 'affected_services': priority, 'evidence': evidence(event, x[i]), 'runbook': book, 'source_mode': event.get('source_mode', 'external'), 'diagnosis_scope': 'heuristic hypothesis from observed signals and declared topology'}
                    self.incidents.appendleft(incident)
                    self.journal.append('incident', incident)
                    self.latched[service] = True
                    self.last_alert[service] = t
                    created.append(incident)
                self.journal.event(event)
            self.accepted += len(accepted)
            self.last_received = time.monotonic()
            self.journal.commit()
            elapsed = (time.perf_counter()-started)*1000
            self.latencies.append(elapsed)
            top = self.services.get('urgent-results', self.services[accepted[-1]['service']])
            self.chart.append({'time': top['event_time'], 'latency': top['latency_p95_ms'], 'risk': top['forecast_risk'], 'pool': top['pool_used'], 'breached': top['breached']})
            return created

    def snapshot(self):
        with self.lock:
            age = time.monotonic()-self.last_received if self.last_received is not None else None
            return {'services': list(self.services.values()), 'incidents': list(self.incidents), 'chart': list(self.chart), 'accepted': self.accepted, 'duplicates': self.duplicates, 'rejected': self.rejected, 'receipt_age_seconds': round(age, 2) if age is not None else None, 'stale': age is None or age > 5, 'model_status': self.model_status, 'model': self.bundle.manifest, 'policy': self.bundle.state['policy'], 'latency_p95_ms': round(float(np.percentile(self.latencies,95)),2) if self.latencies else None, 'dependencies': DEPENDENCIES, 'priorities': PRIORITIES}

    def close(self):
        self.journal.close()
