import os

import redis
from flask import Flask, request, jsonify
from redis import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS'))

class RedisManager:
    _pool = None

    @classmethod
    def get_redis(cls):
        if cls._pool is None:
            cls._pool = ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                max_connections=REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return redis.Redis(connection_pool=cls._pool)

app = Flask(__name__)

def set_flag_in_redis(value: bool):
    redis_client = RedisManager.get_redis()
    redis_client.set("cap_solver_flag", str(value))

@app.route("/start-cpatch", methods=["POST"])
def start_cpatch_route():
    set_flag_in_redis(True)
    data = request.get_json(force=True, silent=True) or {}
    return jsonify({
        "message": "Капча-решатель запущен",
        "you_sent": data
    })

@app.route("/stop-cpatch", methods=["POST"])
def stop_cpatch_route():
    set_flag_in_redis(False)
    data = request.get_json(force=True, silent=True) or {}
    return jsonify({
        "message": "Капча-решатель остановлен",
        "you_sent": data
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)