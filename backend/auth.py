"""Authentication routes - login, signup, JWT token verification."""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone
from config import users_col, JWT_SECRET, JWT_ALGO

auth_bp = Blueprint('auth', __name__, url_prefix='/api/users')


@auth_bp.route('/login', methods=['POST'])
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
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    return jsonify({
        "user_id": str(user.get('_id')),
        "xp": user.get('xp', 0),
        "status": "success",
        "token": token
    })


@auth_bp.route('/signup', methods=['POST'])
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


@auth_bp.route('/me', methods=['GET'])
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
