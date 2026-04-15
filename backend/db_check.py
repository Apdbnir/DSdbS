import json
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

db = config['database']

def check_database_exists():
    try:
        import pg8000
        conn = pg8000.connect(
            host=str(db['host']),
            port=int(db['port']),
            database='postgres',
            user=str(db['user']),
            password=str(db['password'])
        )
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (db['name'],))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists
    except Exception as e:
        print(f'Failed to check database existence: {e}')
        return False

if __name__ == '__main__':
    exists = check_database_exists()
    if exists:
        sys.exit(0)
    else:
        print(f"Database '{db['name']}' not found.")
        sys.exit(1)
