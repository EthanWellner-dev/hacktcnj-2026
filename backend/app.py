from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import re

# PyJWT is required; avoid installing the similarly named `jwt` package
try:
    import jwt
    if not hasattr(jwt, 'encode'):
        raise ImportError("'jwt' module has no encode - likely installed wrong package (jwt). Please uninstall jwt and install PyJWT.")
except ImportError as e:
    raise ImportError("PyJWT is required: pip install PyJWT") from e

# Gemini API
try:
    import google.genai as genai
except ImportError:
    raise ImportError("google-genai is required: pip install google-genai")

from datetime import datetime, timedelta, timezone

# install dependencies: pip install flask flask-cors pymongo PyJWT

# Conversation starters for variety
CONVERSATION_STARTERS = [
    "That movie was actually wild, I didn't expect that ending.",
    "Have you seen any good movies lately?",
    "I just finished this show and it blew my mind.",
    "What's your take on good storytelling in films?",
    "I'm always looking for recommendations on what to watch next."
]

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

# Helper function to extract JSON from response (handles mixed prose + JSON)
def extract_json_from_response(response_text):
    """Extract JSON object from response that may contain prose."""
    # Try direct parse first
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    # Remove markdown code blocks
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    # Try again after stripping markdown
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    # Use regex to find JSON object in the text
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise json.JSONDecodeError("Could not extract valid JSON from response", response_text, 0)

# Load Gemini API key from secrets.env
def load_api_key():
    secrets_path = os.path.join(os.path.dirname(__file__), 'secrets.env')
    if not os.path.exists(secrets_path):
        return None
    try:
        with open(secrets_path, 'r') as f:
            for line in f:
                if line.startswith('Gemini_Api_Key='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error loading Gemini API key: {e}")
    return None

GEMINI_API_KEY = load_api_key()
GEMINI_CLIENT = None
if GEMINI_API_KEY:
    GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)



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

    if not GEMINI_CLIENT:
        return jsonify({'status': 'error', 'message': 'gemini api not configured'}), 500

    payload = request.get_json() or {}
    module = payload.get('module')
    user_msg = payload.get('user_message', '')
    context = payload.get('context', '')
    scenario = payload.get('scenario', '')
    starter = payload.get('starter', '')
    turn_count = payload.get('turn_count', 1)
    
    # Module 6 specific parameters
    pitch_duration = payload.get('pitchDuration', 20)
    hesitation_count = payload.get('hesitationCount', 0)
    filler_count = payload.get('fillerCount', 0)

    if not module or not user_msg:
        return jsonify({'status': 'error', 'message': 'module and user_message required'}), 400

    # Build module-specific prompt for Gemini
    # For hint module, check if we're in early turns (1-2) that need responses, not evaluation
    is_hint_response_turn = (module == 'hint' and turn_count < 3)
    
    prompts = {
        'icebreaker': f"""You are a kind, encouraging evaluator helping neurodivergent kids practice social skills. Make sure you refer to the user as "you" and "your" (etc.) in json responses as they will see your responses.

SCENARIO: {scenario}
User message: \\"{user_msg}\\"

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT. STRICTLY JSON ONLY.

Score generously: minimum 50% unless mean/rude. 50-69% decent, 70-84% good, 85-100% excellent.
XP: +25-40 (decent), +50-75 (good), +100+ (excellent).

{{
  "passed": boolean,
  "score": number,
  "xp": number,
  "feedback": "positive feedback focusing on what they did well",
  "ai_response": "suggested reply from the person"
}}
""",
        
        'hint_response': f"""You are a warm AI companion named Jordan having a casual conversation with a user.

Conversation started with: \\"{starter}\\"

Previous exchange:
{context}

User just said: \\"{user_msg}\\"

Respond naturally and warmly to keep the conversation going. Then provide light, positive commentary about how they're engaging. Keep it encouraging and positive.

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT. STRICTLY JSON ONLY.

{{
  "response": "your conversational response to keep chat going",
  "pontage": "1-2 sentences of light positive commentary on their engagement"
}}
""",
        
        'hint': f"""You are a kind evaluator helping neurodivergent kids recognize social cues.

Turn {turn_count} of conversation between user and Jordan.
The conversation topic: {starter}

Jordan just gave a departure hint: "Yeah for sure... Anyway, wow look at the time, I have an early morning tomorrow."
User replied: \\"{user_msg}\\"

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT. STRICTLY JSON ONLY.

Score: 50-64% recognizes hint, 65-79% good exit, 80-100% excellent graceful exit.
XP: +15-25 (recognizes), +30-40 (good), +50+ (excellent), 0-10 (polite miss).

{{
  "passed": boolean,
  "score": number,
  "xp": number,
  "feedback": "encouraging feedback on their social awareness"
}}
""",
        
        'pingpong': f"""You are a kind evaluator helping neurodivergent kids maintain conversation momentum.

Opening: "So what do you usually do for fun on the weekends?"
Full conversation so far:
{context}

User's latest reply: \\"{user_msg}\\"

SCORING GUIDELINES - Be generous and supportive:
- Score 50-64%: Message shows some engagement but is short/closed-ended (one-word, yes/no, or dies out)
- Score 65-79%: Good momentum - shares thoughts and asks a follow-up question, keeps it going
- Score 80-100%: Excellent - warm, detailed response that asks open-ended questions and flows naturally

XP Awards:
- +10-20: Short/closed attempts (50-64%)
- +30-50: Good momentum (65-79%)
- +60+: Excellent conversation flow (80-100%)

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT. STRICTLY JSON ONLY.

{{
  "passed": boolean,
  "score": number,
  "xp": number,
  "feedback": "encouraging feedback on their conversational skills",
  "ai_response": "suggested continuation from partner"
}}
""",

        'module6': f"""You are a warm, encouraging mentor helping neurodivergent children build confidence in public speaking. This is a safe, judgment-free space for them to practice. Remember that many neurodivergent learners experience:
- Social anxiety and presentation nerves
- Difficulty with real-time verbal fluency
- Sensory processing challenges that affect delivery
- Intrusive negative thoughts despite their actual performance

Your job is to celebrate their effort, build confidence, and offer constructive encouragement. Be genuinely kind and affirming.

THEIR PITCH (elevator introduction):
\\"{user_msg}\\"

CONTEXT: They recorded this pitch for {pitch_duration} seconds. They had {hesitation_count} pauses longer than 1.5 seconds and {filler_count} filler words (um/uh/like).

SCORING GUIDELINES - Score with compassion and celebration:
- Score 50-59%: They showed courage just by doing this! Acknowledge effort, identify one small win, suggest one gentle improvement.
- Score 60-74%: They did well! Highlight what was authentic or engaging, acknowledge their bravery.
- Score 75-89%: Really good work! Praise specific strengths (clarity, enthusiasm, structure, eye-contact simulation via vocal warmth).
- Score 90-100%: Excellent! They nailed it—praise their confidence, delivery, and authenticity.

XP Awards - Be generous, focus on effort and improvement:
- 50-59%: +25-35 (celebration of trying)
- 60-74%: +40-55 (solid work)
- 75-89%: +60-80 (great job)
- 90-100%: +90-120 (excellent effort and delivery)

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT. STRICTLY JSON ONLY.

{{
  "passed": boolean,
  "score": number,
  "xp": number,
  "feedback": "warm, supportive feedback celebrating what they did well and offering one gentle, actionable suggestion for next time"
}}
"""
    }

    if module not in prompts and not is_hint_response_turn:
        return jsonify({'status': 'error', 'message': 'invalid module'}), 400
    
    prompt_key = 'hint_response' if is_hint_response_turn else module

    try:
        # use flash-lite model with token limit
        response = GEMINI_CLIENT.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompts[prompt_key]
        )
        
        # Parse response - extract JSON even if there's prose mixed in
        response_text = response.text.strip()
        result = extract_json_from_response(response_text)
        
        # Handle hint response turns differently (just return response + pontage, no XP yet)
        if is_hint_response_turn:
            return jsonify({
                'status': 'success',
                'response': result.get('response', ''),
                'pontage': result.get('pontage', ''),
                'xp_current': user.get('xp', 0)
            })
        
        # For evaluation turns, award XP if present
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
        return jsonify({'status': 'error', 'message': 'invalid gemini response format'}), 500
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
