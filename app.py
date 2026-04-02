import ssl
import time
from flask import Flask, jsonify
from flask_cors import CORS
from config import PORT, SSL_CERT_PATH, SSL_KEY_PATH, DB_PATH
from db import init_db

_start_time = time.time()

def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    CORS(app)
    db = db_path or DB_PATH
    init_db(db)
    app.config["DB_PATH"] = db

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "uptime_seconds": round(time.time() - _start_time),
        })

    @app.route("/")
    def dashboard():
        return app.send_static_file("index.html")

    from api.reports import bp as reports_bp
    from api.threads import bp as threads_bp
    from api.tags import bp as tags_bp
    from api.moc import bp as moc_bp
    from api.stats import bp as stats_bp

    app.register_blueprint(reports_bp)
    app.register_blueprint(threads_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(moc_bp)
    app.register_blueprint(stats_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
    app.run(host="0.0.0.0", port=PORT, ssl_context=ssl_ctx, debug=False)
