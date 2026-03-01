"""Module 6 (Confidence Calibration - Pitch Exercise) routes."""

from flask import Blueprint, request, jsonify
import jwt
from config import users_col, JWT_SECRET, JWT_ALGO

module6_bp = Blueprint('module6', __name__, url_prefix='/api/module6')


@module6_bp.route('/complete', methods=['POST'])
def complete():
    """Record completion of module 6 and award xp.

    Expects JSON body with numeric ``xp`` field. Requires a valid
    Bearer token similar to ``/api/users/me``. The user's xp value is
    incremented and the new total is returned.
    """
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

    payload = request.get_json() or {}
    xp_gain = payload.get('xp', 0)
    try:
        xp_gain = int(xp_gain)
    except Exception:
        return jsonify({'status': 'error', 'message': 'xp must be an integer'}), 400

    if xp_gain <= 0:
        return jsonify({'status': 'error', 'message': 'xp must be positive'}), 400

    users_col.update_one({'username': user['username']}, {'$inc': {'xp': xp_gain}})
    new_user = users_col.find_one({'username': user['username']})
    return jsonify({'status': 'success', 'xp': new_user.get('xp', 0)})
