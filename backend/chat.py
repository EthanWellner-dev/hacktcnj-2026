"""Chat evaluation routes - evaluate user chat messages using AI."""

from flask import Blueprint, request, jsonify
import jwt
import json
from datetime import datetime, timezone
from config import users_col, training_col, JWT_SECRET, JWT_ALGO, GEMINI_CLIENT
from utils import extract_json_from_response

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/evaluate', methods=['POST'])
def evaluate():
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


@chat_bp.route('/analyze', methods=['POST'])
def analyze_chat():
    """Analyze selected text from chat."""
    data = request.get_json() or {}
    module_type = data.get('module_type')
    selected_text = data.get('selected_text')
    # return mocked analysis
    return jsonify({
        "passed": True,
        "score": 85,
        "feedback": "Good job identifying the passive aggression!"
    })
