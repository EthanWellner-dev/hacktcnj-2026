"""Training result submission and tracking."""

from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timezone
from config import users_col, training_col, JWT_SECRET, JWT_ALGO

training_bp = Blueprint('training', __name__, url_prefix='/api/training')


@training_bp.route('/submit', methods=['POST'])
def submit():
    """Record a generic training result and optionally award XP.

    Request JSON should contain ``module`` (string) and ``results`` (object).
    ``results`` may include an ``xp`` field which will be added to the user's
    XP total.  Other metrics are stored for future analysis.
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
    module_name = payload.get('module')
    results = payload.get('results', {})
    if not module_name or not isinstance(results, dict):
        return jsonify({'status': 'error', 'message': 'module and results required'}), 400

    xp_gain = 0
    if 'xp' in results:
        try:
            xp_gain = int(results.get('xp', 0))
        except Exception:
            return jsonify({'status': 'error', 'message': 'xp must be an integer'}), 400
        if xp_gain < 0:
            return jsonify({'status': 'error', 'message': 'xp cannot be negative'}), 400

    # persist the training record
    record = {
        'username': user['username'],
        'module': module_name,
        'results': results,
        'xp_awarded': xp_gain,
        'timestamp': datetime.now(timezone.utc)
    }
    training_col.insert_one(record)

    # update xp if necessary
    if xp_gain > 0:
        users_col.update_one({'username': user['username']}, {'$inc': {'xp': xp_gain}})
        user = users_col.find_one({'username': user['username']})

    return jsonify({'status': 'success', 'xp': user.get('xp', 0)})
