from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        dbname='mydatabase',
        user='postgres',
        password='your-password',
        host='postgres-slave-service'
    )


@app.route('/health/<app_name>', methods=['GET'])
def get_health(app_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM health_status WHERE app_name = %s', (app_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    health_status = []
    for row in rows:
        health_status.append({
            'id': row[0],
            'app_name': row[1],
            'failure_count': row[2],
            'success_count': row[3],
            'last_failure': row[4],
            'last_success': row[5],
            'created_at': row[6]
        })

    return jsonify(health_status)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
