from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os

# PyJWT is required; avoid installing the similarly named `jwt` package
try:
    import jwt
    if not hasattr(jwt, 'encode'):
        raise ImportError("'jwt' module has no encode - likely installed wrong package (jwt). Please uninstall jwt and install PyJWT.")
except ImportError as e:
    raise ImportError("PyJWT is required: pip install PyJWT") from e

from datetime import datetime, timedelta, timezone

# install dependencies: pip install flask flask-cors pymongo PyJWT

# serve templates from `template/` and static from `template/static`
app = Flask(__name__, static_folder='../template/static', template_folder='../template')
CORS(app)  # allow all origins by default for local development

# database configuration – expects MONGODB_URI env var or defaults to localhost
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://etwellner_db_user:J6pk1WJJJeB4lvt5@init.4uvaz3g.mongodb.net/')
client = MongoClient(MONGO_URI)
db = client.social_sandbox
users_col = db.users
training_col = db.training_results  # store detailed training submissions

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


@app.route('/modules')
def modules_page():
    return render_template('modules.html')


# simple endpoint for the first real training module (module 6)
@app.route('/module6')
def module6_page():
    # serve the new confidence calibration pitch exercise
    return render_template('module6.html')


@app.route('/api/module6/complete', methods=['POST'])
def module6_complete():
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
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
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


@app.route('/api/training/submit', methods=['POST'])
def training_submit():
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
