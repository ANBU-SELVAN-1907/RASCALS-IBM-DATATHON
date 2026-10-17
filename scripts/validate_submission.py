from pathlib import Path
import hashlib
import json
import re

root=Path(__file__).resolve().parents[1]
text=(root/'submission/FORM-ANSWERS.md').read_text(encoding='utf-8')
blocks=re.findall(r'```text\n(.*?)\n```',text,re.S)
assert len(blocks)==5
for index,block in enumerate(blocks,1):
    assert len(block)<=1024,(index,len(block))
    print('Form field',index,':',len(block),'/ 1024 characters')
manifest=json.loads((root/'artifacts/manifest.json').read_text())
assert hashlib.sha256((root/'artifacts/models.joblib').read_bytes()).hexdigest()==manifest['sha256']
for filename in ('01_train_and_evaluate','02_test_and_benchmark'):
    state=json.loads((root/f'notebooks/{filename}.execution.json').read_text())
    assert state['state']=='success',state
    print('Executed notebook:',filename,state['state'])
for file in root.rglob('*'):
    if not file.is_file() or '.git' in file.parts:
        continue
    assert file.suffix.lower() not in {'.pem','.key'},file
print('Model integrity and publication checks passed.')
