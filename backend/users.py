"""User-related API routes - leaderboard, user stats."""

from flask import Blueprint, jsonify, request
import jwt
from config import users_col, JWT_SECRET, JWT_ALGO

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# Mock users for hackathon demo
MOCK_USERS = [
    {
        '_id': 'mock-1',
        'username': 'Alex_Gaming',
        'age': 24,
        'gender': 'male',
        'persona': 'job_seeker',
        'hobbies': ['gaming', 'music', 'tech'],
        'bio': 'Love connecting with people and learning new things',
        'xp': 450,
        'is_mock': True
    },
    {
        '_id': 'mock-2',
        'username': 'Jordan_Arts',
        'age': 22,
        'gender': 'non-binary',
        'persona': 'awkward_texter',
        'hobbies': ['reading', 'cooking', 'art'],
        'bio': 'Always up for interesting conversations',
        'xp': 320,
        'is_mock': True
    },
    {
        '_id': 'mock-3',
        'username': 'Casey_Tech',
        'age': 26,
        'gender': 'female',
        'persona': 'conflict_avoider',
        'hobbies': ['sports', 'fitness', 'travel', 'tech'],
        'bio': 'Passionate about tech and fitness',
        'xp': 580,
        'is_mock': True
    },
    {
        '_id': 'mock-4',
        'username': 'Morgan_Fit',
        'age': 21,
        'gender': 'female',
        'persona': 'job_seeker',
        'hobbies': ['fitness', 'cooking', 'travel'],
        'bio': 'Creative soul looking for like-minded friends',
        'xp': 275,
        'is_mock': True
    },
    {
        '_id': 'mock-5',
        'username': 'Riley_Books',
        'age': 23,
        'gender': 'male',
        'persona': 'awkward_texter',
        'hobbies': ['reading', 'music', 'art', 'tech'],
        'bio': 'Fitness enthusiast and travel junkie',
        'xp': 410,
        'is_mock': True
    }
]


def calculate_compatibility(user1, user2):
    """Calculate compatibility score between two users (0-100)."""
    score = 50  # Base score
    
    # Age proximity (±5 years = +10)
    age1, age2 = user1.get('age'), user2.get('age')
    if age1 and age2 and abs(age1 - age2) <= 5:
        score += 10
    
    # Shared hobbies
    hobbies1 = set(user1.get('hobbies', []))
    hobbies2 = set(user2.get('hobbies', []))
    shared = hobbies1 & hobbies2
    if shared:
        score += min(20, len(shared) * 8)  # Max +20
    
    # Different personas can be good (variety)
    if user1.get('persona') != user2.get('persona'):
        score += 5
    
    # Cap at 100
    return min(100, score)


@users_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    """Fetch top users by XP."""
    cursor = users_col.find({}, {"username": 1, "xp": 1}).sort("xp", -1).limit(10)
    result = [{"name": u.get('username'), "xp": u.get('xp', 0)} for u in cursor]
    return jsonify(result)


@users_bp.route('/search', methods=['GET'])
def search_users():
    """Search for users by username or interests.
    
    Query params:
    - q: search query (optional)
    - include_self: include current user (default false)
    - limit: results limit (default 20)
    - include_mock: include mock users (default true)
    """
    auth = request.headers.get('Authorization', '')
    current_user = None
    
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            current_user = users_col.find_one({'username': data.get('username')})
        except Exception:
            pass
    
    query = request.args.get('q', '').strip().lower()
    include_self = request.args.get('include_self', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 20))
    include_mock = request.args.get('include_mock', 'true').lower() == 'true'
    
    results = []
    
    # Search real users
    if query:
        db_users = list(users_col.find({
            'username': {'$regex': query, '$options': 'i'}
        }).limit(limit))
    else:
        db_users = list(users_col.find({}).limit(limit))
    
    # Filter out current user if not requested
    for user in db_users:
        if not include_self and current_user and str(user['_id']) == str(current_user['_id']):
            continue
        user['_id'] = str(user['_id'])
        user['is_mock'] = False
        user['compatibility'] = calculate_compatibility(current_user, user) if current_user else 75
        results.append(user)
    
    # Add mock users if requested
    if include_mock:
        for mock_user in MOCK_USERS:
            if query and query not in mock_user['username'].lower():
                continue
            mock_copy = mock_user.copy()
            mock_copy['compatibility'] = calculate_compatibility(current_user, mock_user) if current_user else 75
            results.append(mock_copy)
    
    return jsonify({
        'status': 'success',
        'users': results[:limit],
        'count': len(results[:limit])
    })


@users_bp.route('/matching/get-matches', methods=['GET'])
def get_matches():
    """Get matched users for chat (2-5 people).
    
    Uses compatibility scoring and shared interests.
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

    # Get all users except current
    other_users = list(users_col.find({
        'username': {'$ne': user['username']}
    }))
    
    # Calculate compatibility with all users
    scored_users = []
    for other_user in other_users:
        other_user['_id'] = str(other_user['_id'])
        compatibility = calculate_compatibility(user, other_user)
        scored_users.append({**other_user, 'compatibility': compatibility})
    
    # Add mock users
    for mock_user in MOCK_USERS:
        compatibility = calculate_compatibility(user, mock_user)
        scored_users.append({**mock_user, 'compatibility': compatibility})
    
    # Sort by compatibility and select 2-5
    scored_users.sort(key=lambda x: x['compatibility'], reverse=True)
    num_matches = min(5, max(2, len(scored_users)))
    matches = scored_users[:num_matches]
    
    return jsonify({
        'status': 'success',
        'matches': matches,
        'count': len(matches)
    })
