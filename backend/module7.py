"""Module 7 (The Emotion Matrix - Multimodal Emotion Detection) routes."""

from flask import Blueprint, request, jsonify
import jwt
from config import users_col, JWT_SECRET, JWT_ALGO
from datetime import datetime

module7_bp = Blueprint('module7', __name__, url_prefix='/api/module7')


@module7_bp.route('/complete', methods=['POST'])
def complete():
    """Record completion of module 7 and award xp.

    Expects JSON body with:
    - xp: integer XP earned
    - accuracy: integer accuracy percentage (0-100)
    - correctCount: integer number of correct answers
    - totalAnswered: integer total answers given
    - timestamp: ISO datetime string

    Requires a valid Bearer token. The user's xp value is incremented
    and the new total is returned.
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
    accuracy = payload.get('accuracy', 0)
    correct_count = payload.get('correctCount', 0)
    total_answered = payload.get('totalAnswered', 0)
    timestamp = payload.get('timestamp', datetime.now().isoformat())

    # Validate inputs
    try:
        xp_gain = int(xp_gain)
        accuracy = int(accuracy)
        correct_count = int(correct_count)
        total_answered = int(total_answered)
    except Exception:
        return jsonify({'status': 'error', 'message': 'invalid input types'}), 400

    if xp_gain < 0:
        return jsonify({'status': 'error', 'message': 'xp must be non-negative'}), 400
    
    if not (0 <= accuracy <= 100):
        return jsonify({'status': 'error', 'message': 'accuracy must be between 0 and 100'}), 400

    # Record the module completion
    module_record = {
        'module': 'module7',
        'xp_earned': xp_gain,
        'accuracy': accuracy,
        'correct_count': correct_count,
        'total_answered': total_answered,
        'timestamp': timestamp
    }

    # Update user document
    users_col.update_one(
        {'username': user['username']},
        {
            '$inc': {'xp': xp_gain},
            '$push': {'module_history': module_record},
            '$set': {'last_activity': datetime.now().isoformat()}
        }
    )

    # Retrieve updated user
    updated_user = users_col.find_one({'username': user['username']})
    
    return jsonify({
        'status': 'success',
        'xp': updated_user.get('xp', 0),
        'accuracy': accuracy,
        'message': f'Module 7 completed with {accuracy}% accuracy'
    })
