from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

# Database connection settings
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 1234)
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_HOST = os.getenv('POSTGRES_HOST', 'local')


@app.route('/health/<app_name>', methods=['GET'])
def get_health(app_name):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password=1234,
            host='localhost'
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, app_name, failure_count, success_count, last_failure, last_success, created_at
            FROM app_health
            WHERE app_name = %s
        """, (app_name,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'app_name': row[1],
                'failure_count': row[2],
                'success_count': row[3],
                'last_failure': row[4],
                'last_success': row[5],
                'created_at': row[6]
            })
        return jsonify(result)
    except Exception as e:
        return str(e), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
