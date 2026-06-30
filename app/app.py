import os
import time
from flask import Flask, jsonify, request
import psycopg2
import redis

app = Flask(__name__)

# --- Postgres connection settings (from environment variables) ---
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_NAME = os.environ.get('DB_NAME', 'appdb')
DB_USER = os.environ.get('DB_USER', 'appuser')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'apppass')

# --- Redis connection settings ---
REDIS_HOST = os.environ.get('REDIS_HOST', 'cache')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_db_connection(retries=10, delay=2):
    """Postgres can take a moment to be ready -- retry until it accepts connections."""
    last_error = None
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
            )
            return conn
        except psycopg2.OperationalError as e:
            last_error = e
            time.sleep(delay)
    raise last_error


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            note TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


@app.route('/')
def home():
    return jsonify({
        'message': 'Multi-container Flask + Postgres + Redis demo',
        'endpoints': ['/visits [GET, POST]', '/cache-demo', '/health']
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/visits', methods=['GET', 'POST'])
def visits():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        note = request.json.get('note', '') if request.is_json else ''
        cur.execute("INSERT INTO visits (note) VALUES (%s) RETURNING id", (note,))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'inserted_id': new_id}), 201

    cur.execute("SELECT id, note, created_at FROM visits ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {'id': row[0], 'note': row[1], 'created_at': str(row[2])} for row in rows
    ])


@app.route('/cache-demo')
def cache_demo():
    """Shows Redis caching: counts how many times this endpoint has been hit."""
    count = r.incr('cache_demo_hits')
    return jsonify({'hits_since_startup': count})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
