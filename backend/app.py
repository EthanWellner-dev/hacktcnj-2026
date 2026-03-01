"""
Main Flask application entry point with blueprint registration.
All application configuration and API routes are modularized into separate files.
"""

from flask import Flask
from flask_cors import CORS

# serve templates from `template/` and static from `template/static`
app = Flask(__name__, static_folder='../template/static', template_folder='../template')
CORS(app)  # allow all origins by default for local development

# Suppress favicon 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204

# Import all blueprints
from auth import auth_bp
from views import views_bp
from users import users_bp
from training import training_bp
from chat import chat_bp
from module5 import module5_bp
from module6 import module6_bp
from module7 import module7_bp
from module8 import module8_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(views_bp)
app.register_blueprint(users_bp)
app.register_blueprint(training_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(module5_bp)
app.register_blueprint(module6_bp)
app.register_blueprint(module7_bp)
app.register_blueprint(module8_bp)

if __name__ == '__main__':
    app.run('127.0.0.1', port=5000, debug=True)