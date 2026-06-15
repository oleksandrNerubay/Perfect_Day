from flask import Flask
from flask_sock import Sock

import config
from db.schema import ensure_indexes
from routes.session import bp as session_bp
from routes.transcribe import bp as transcribe_bp, sock as transcribe_sock
from routes.transcript import bp as transcript_bp
from routes.classify import bp as classify_bp
from routes.recommend import bp as recommend_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = config.FLASK_SECRET_KEY

    transcribe_sock.init_app(app)

    app.register_blueprint(session_bp)
    app.register_blueprint(transcribe_bp)
    app.register_blueprint(transcript_bp)
    app.register_blueprint(classify_bp)
    app.register_blueprint(recommend_bp)

    ensure_indexes()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True, threaded=True)
