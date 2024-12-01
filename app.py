from flask import Flask
from routes.chatbot_routes import chatbot_bp
from dotenv import load_dotenv
import os
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)