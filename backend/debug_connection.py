import json
import os

path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(path, 'rb') as f:
    raw = f.read()
print('raw bytes length', len(raw))
print('raw bytes repr', raw[:200])
try:
    text = raw.decode('utf-8')
    print('decoded ok')
except Exception as e:
    print('decode utf8 failed', repr(e))
    text = raw.decode('utf-8', errors='replace')
    print(text)
config = json.loads(text)
for key, value in config['database'].items():
    print(key, repr(value), type(value), len(value))
print('env PG variables:')
for k, v in sorted(os.environ.items()):
    if k.startswith('PG') or k.lower().startswith('pg'):
        print(k, repr(v))
print('PATH first 200', repr(os.environ.get('PATH', '')[:200]))
