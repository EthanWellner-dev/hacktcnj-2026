from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

# PyJWT is required; avoid installing the similarly named `jwt` package
try:
    import jwt
    if not hasattr(jwt, 'encode'):
        raise ImportError("'jwt' module has no encode - likely installed wrong package (jwt). Please uninstall jwt and install PyJWT.")
except ImportError as e:
    raise ImportError("PyJWT is required: pip install PyJWT") from e

# Gemini API
try:
    import google.generativeai as genai
except ImportError:
    raise ImportError("google-generativeai is required: pip install google-generativeai")

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

# Load Gemini API key from secrets.env
def load_api_key():
    secrets_path = os.path.join(os.path.dirname(__file__), 'secrets.env')
    if not os.path.exists(secrets_path):
        return None
    try:
        with open(secrets_path, 'r') as f:
            for line in f:
                if line.startswith('Gemini-Api-Key:'):
                    return line.split(':', 1)[1].strip()
    except Exception as e:
        print(f"Error loading Gemini API key: {e}")
    return None

GEMINI_API_KEY = load_api_key()
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)



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


@app.route('/module6')
def module6_page():
    # serve the new confidence calibration pitch exercise
    return render_template('module6.html')


@app.route('/module1')
def module1_page():
    return render_template('module1.html')


@app.route('/module2')
def module2_page():
    return render_template('module2.html')


@app.route('/module3')
def module3_page():
    return render_template('module3.html')


@app.route('/module4')
def module4_page():
    return render_template('module4.html')



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


@app.route('/api/chat/evaluate', methods=['POST'])
def chat_evaluate():
    """Evaluate a user's chat message using Gemini AI.
    
    Request JSON:
    {
        "module": "icebreaker|hint|pingpong",
        "user_message": "user's response",
        "context": "previous conversation"
    }
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

    if not GEMINI_API_KEY:
        return jsonify({'status': 'error', 'message': 'gemini api not configured'}), 500

    payload = request.get_json() or {}
    module = payload.get('module')
    user_msg = payload.get('user_message', '')
    context = payload.get('context', '')

    if not module or not user_msg:
        return jsonify({'status': 'error', 'message': 'module and user_message required'}), 400

    # Build module-specific prompt for Gemini
    prompts = {
        'icebreaker': f"""You are evaluating a cold networking message. The user just met someone at a tech conference and received their business card.

Context: The other person's name is Alex from the tech conference.
User's message: "{user_msg}"

Evaluate if this message:
1. Establishes rapport and shared context
2. Shows genuine interest without being pushy
3. Is appropriate length (not too brief)

Respond with ONLY valid JSON (no markdown, no extra text):
{{"passed": true or false, "score": 0-100, "xp": 0-100, "feedback": "string", "ai_response": "what Alex might reply"}}""",
        
        'hint': f"""You are evaluating if the user picked up on a social cue to end a conversation gracefully.

Context: You (the AI character Jordan) just hinted that you want to leave by saying: 'Yeah for sure... Anyway, wow look at the time, I have an early morning tomorrow.'
User's response: "{user_msg}"

Evaluate if the user:
1. Recognized the hint to leave
2. Provided a graceful, polite exit
3. Did not try to extend the conversation

Respond with ONLY valid JSON (no markdown, no extra text):
{{"passed": true or false, "score": 0-100, "xp": 0-100, "feedback": "string"}}""",
        
        'pingpong': f"""You are evaluating conversational momentum. The initial prompt was: 'So what do you usually do for fun on the weekends?'

Context: {context}
User's latest response: "{user_msg}"

Evaluate if the user:
1. Asked open-ended questions (not yes/no)
2. Provided substantive replies (not one-word)
3. Kept the conversation flowing

Respond with ONLY valid JSON (no markdown, no extra text):
{{"passed": true or false, "score": 0-100, "xp": 0-100, "feedback": "string", "ai_response": "next thing to say to keep conversation going"}}"""
    }

    if module not in prompts:
        return jsonify({'status': 'error', 'message': 'invalid module'}), 400

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompts[module])
        
        # Parse response
        response_text = response.text.strip()
        # Remove markdown code block if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        
        # Award XP if present
        xp_gain = result.get('xp', 0)
        if xp_gain > 0:
            users_col.update_one({'username': user['username']}, {'$inc': {'xp': xp_gain}})
            user = users_col.find_one({'username': user['username']})
        
        # Record training result
        record = {
            'username': user['username'],
            'module': module,
            'results': {
                'user_message': user_msg,
                'score': result.get('score', 0),
                'passed': result.get('passed', False),
                'xp': xp_gain
            },
            'xp_awarded': xp_gain,
            'timestamp': datetime.now(timezone.utc)
        }
        training_col.insert_one(record)
        
        result['xp_current'] = user.get('xp', 0)
        return jsonify({'status': 'success', **result})
    except json.JSONDecodeError as je:
        print(f"JSON parse error: {je}, response was: {response_text}")
        return jsonify({'status': 'error', 'message': 'invalid gemini response'}), 500
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
