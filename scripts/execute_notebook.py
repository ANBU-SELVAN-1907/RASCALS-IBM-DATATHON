"""Execute a project notebook through a Jupyter kernel, retaining live progress."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import time
import nbformat
from nbclient import NotebookClient

root = Path.cwd().resolve()
source = (root / sys.argv[1]).resolve()
source.relative_to(root)
output = source.with_name(source.stem + '.executed.ipynb')
record = source.with_suffix('.execution.json')
notebook = nbformat.read(source, as_version=4)
for cell in notebook.cells:
    if cell.cell_type == 'code':
        cell.outputs = []
        cell.execution_count = None
state = {'notebook': str(source.relative_to(root)), 'started_utc': datetime.now(timezone.utc).isoformat(), 'state': 'running', 'completed_cells': 0}
started = time.monotonic()

def progress(cell, cell_index, **kwargs):
    state['completed_cells'] += 1
    state['last_completed_cell_index'] = cell_index
    state['elapsed_seconds'] = round(time.monotonic()-started, 2)
    record.write_text(json.dumps(state, indent=2))
    nbformat.write(notebook, output)
    print('Completed cell', cell_index, flush=True)

client = NotebookClient(notebook, timeout=1800, kernel_name='python3', resources={'metadata': {'path': str(source.parent)}}, on_cell_executed=progress)
try:
    client.execute()
    state['state'] = 'success'
except Exception as exc:
    state['state'] = 'failed'
    state['error'] = str(exc)[-4000:]
finally:
    state['elapsed_seconds'] = round(time.monotonic()-started, 2)
    state['finished_utc'] = datetime.now(timezone.utc).isoformat()
    nbformat.write(notebook, output)
    record.write_text(json.dumps(state, indent=2))
    print(json.dumps(state, indent=2), flush=True)
if state['state'] != 'success':
    raise SystemExit(1)
