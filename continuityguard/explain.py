"""Local constrained generation: verified facts and runbook IDs only."""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import threading
import time

class Explainer:
    def __init__(self, model_path, journal):
        self.path = Path(model_path)
        self.journal = journal
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='granite')
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.busy = False
        self.model = None

    def request(self, incident):
        key = incident['id']
        with self.lock:
            if key in self.cache:
                return self.cache[key]
            if self.busy:
                return {'status': 'busy', 'message': 'One local explanation is already running.'}
            self.busy = True
            self.cache[key] = {'status':'generating'}
            self.executor.submit(self._generate, incident)
            return self.cache[key]

    def _generate(self, incident):
        started = time.perf_counter()
        service, book = incident['service'], incident['runbook']
        items = incident['evidence']
        facts = '; '.join(f"{e['label']} {e['value']} {e['unit']} ({e['id']})" for e in items)
        summaries = [f"Review {book['id']} for {service}. Observed measurements: {facts}.", f"{service} needs operator investigation. {book['title']}. Supporting measurements: {facts}."]
        fallback = {'summary': summaries[0], 'evidence_ids': [e['id'] for e in items], 'runbook_id': book['id']}
        result = {'status': 'complete', 'mode': 'deterministic fallback', **fallback}
        try:
            from llama_cpp import Llama, LlamaGrammar
            if self.model is None:
                self.model = Llama(model_path=str(self.path), n_ctx=2048, n_batch=128, n_threads=2, verbose=False)
            schema = {'type':'object','properties': {'summary': {'type':'string','enum':summaries}, 'evidence_ids': {'type':'array','items': {'type':'string','enum':fallback['evidence_ids']}, 'minItems':1,'maxItems':3}, 'runbook_id': {'type':'string','enum':[book['id']]}}, 'required':['summary','evidence_ids','runbook_id'], 'additionalProperties':False}
            grammar = LlamaGrammar.from_json_schema(json.dumps(schema), verbose=False)
            prompt = f"Choose a concise evidence-grounded incident explanation. Do not invent facts. Service: {service}. Verified observations: {facts}. Approved runbook: {book['id']} {book['title']}. Return JSON with summary, evidence_ids, runbook_id. Answer:"
            response = self.model.create_completion(prompt, max_tokens=220, temperature=0, grammar=grammar)
            value = json.loads(response['choices'][0]['text'])
            if value['summary'] not in summaries or value['runbook_id'] != book['id'] or not value['evidence_ids'] or not set(value['evidence_ids']) <= set(fallback['evidence_ids']):
                raise ValueError('Generated output failed evidence validation')
            result = {'status':'complete','mode':'local Granite · constrained generation', **value, 'completion_tokens':response.get('usage',{}).get('completion_tokens')}
        except Exception as exc:
            result['fallback_reason'] = type(exc).__name__
        result['elapsed_seconds'] = round(time.perf_counter()-started, 2)
        result['scope'] = 'Generation selects a verified wording under a strict evidence schema; no autonomous action.'
        self.journal.append('explanation', {'incident_id':incident['id'], **result})
        with self.lock:
            self.cache[incident['id']] = result
            while len(self.cache) > 100:
                self.cache.popitem(last=False)
            self.busy = False

    def status(self, incident_id):
        with self.lock:
            return self.cache.get(incident_id, {'status':'not_requested'})

    def close(self):
        self.executor.shutdown(wait=False, cancel_futures=True)
