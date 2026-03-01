"""User-related API routes - leaderboard, user stats."""

from flask import Blueprint, jsonify
from config import users_col

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    """Fetch top users by XP."""
    cursor = users_col.find({}, {"username": 1, "xp": 1}).sort("xp", -1).limit(10)
    result = [{"name": u.get('username'), "xp": u.get('xp', 0)} for u in cursor]
    return jsonify(result)
