from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
import jwt
from datetime import datetime, timedelta

# install dependencies: pip install flask flask-cors pymongo PyJWT

# serve templates from `template/` and static from `template/static`
app = Flask(__name__, static_folder='../template/static', template_folder='../template')
CORS(app)  # allow all origins by default for local development

# database configuration – expects MONGODB_URI env var or defaults to localhost
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://etwellner_db_user:J6pk1WJJJeB4lvt5@init.4uvaz3g.mongodb.net/')
client = MongoClient(MONGO_URI)
db = client.social_sandbox
users_col = db.users

# JWT config
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret')
JWT_ALGO = 'HS256'


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"status": "error", "message": "username and password required"}), 400

    user = users_col.find_one({"username": username})
    if not user or not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({"status": "error", "message": "invalid credentials"}), 401

    # create JWT
    payload = {
        'user_id': str(user.get('_id')),
        'username': user.get('username'),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    return jsonify({
        "user_id": str(user.get('_id')),
        "xp": user.get('xp', 0),
        "status": "success",
        "token": token
    })


@app.route('/api/users/leaderboard', methods=['GET'])
def leaderboard():
    # fetch top users by xp
    cursor = users_col.find({}, {"username": 1, "xp": 1}).sort("xp", -1).limit(10)
    result = [{"name": u.get('username'), "xp": u.get('xp', 0)} for u in cursor]
    return jsonify(result)


@app.route('/api/users/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    persona = data.get('persona')

    if not username or not password or not persona:
        return jsonify({"status": "error", "message": "username, password and persona required"}), 400

    if users_col.find_one({"username": username}):
        return jsonify({"status": "error", "message": "username already taken"}), 409

    pw_hash = generate_password_hash(password)
    user = {
        "username": username,
        "password_hash": pw_hash,
        "persona": persona,
        "xp": 0
    }
    users_col.insert_one(user)
    return jsonify({"status": "success"})


@app.route('/api/analyze_chat', methods=['POST'])
def analyze_chat():
    data = request.get_json() or {}
    module_type = data.get('module_type')
    selected_text = data.get('selected_text')
    # return mocked analysis
    return jsonify({
        "passed": True,
        "score": 85,
        "feedback": "Good job identifying the passive aggression!"
    })


@app.route('/api/users/me', methods=['GET'])
def me():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'status': 'error', 'message': 'missing token'}), 401
    token = auth.split(' ', 1)[1]
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return jsonify({'status': 'error', 'message': 'invalid token'}), 401

    user = users_col.find_one({'username': data.get('username')})
    if not user:
        return jsonify({'status': 'error', 'message': 'user not found'}), 404
    return jsonify({
        'user_id': str(user.get('_id')),
        'username': user.get('username'),
        'xp': user.get('xp', 0),
        'persona': user.get('persona')
    })


if __name__ == '__main__':
    app.run(debug=True)
