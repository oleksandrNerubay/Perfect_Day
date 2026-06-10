from flask import Flask
from routes.users import users_bp
from routes.voice import voice_bp
from routes.ml import ml_bp

app = Flask(__name__)

app.register_blueprint(users_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(ml_bp)

if __name__ == "__main__":
    app.run(debug=True)
