"""Chat evaluation routes - evaluate user chat messages using AI."""

from flask import Blueprint, request, jsonify
import jwt
import json
from datetime import datetime, timezone
from bson import ObjectId
from config import users_col, training_col, JWT_SECRET, JWT_ALGO, GEMINI_CLIENT, chat_messages_col, chat_rooms_col
from utils import extract_json_from_response
from content_filter import contains_harmful_content, filter_message

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
    pitch_duration = payload.get('pitchDuration', 0)
    filler_count = payload.get('fillerCount', 0)
    hesitation_count = payload.get('hesitationCount', 0)

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
        
        'module6': f"""You are a warm, encouraging evaluator helping neurodivergent kids build public speaking confidence.

User's Pitch Transcript:
\\"{user_msg}\\"

Performance Metrics:
- Pitch Duration: {pitch_duration} seconds
- Filler Words (um/uh/like): {filler_count}
- Hesitations (>1.5s pauses): {hesitation_count}

IMPORTANT: Score generously and supportively. MINIMUM SCORE IS 60% unless the pitch is empty/gibberish.
- 60-69%: Attempted the pitch with some filler words or hesitations - keep practicing!
- 70-79%: Good effort! Used clear language with minimal distractions.
- 80-100%: Excellent! Confident, clear, engaging delivery with minimal filler words.

Be encouraging and focus on effort and improvement. Recognize that neurodivergent speakers often need practice to build confidence.

XP Awards (minimum 25 for any attempt):
- 25-40 XP: Completed pitch (60-69%)
- 50-75 XP: Good performance (70-79%)
- 80-100 XP: Excellent performance (80-100%)

RESPOND WITH ONLY VALID JSON. NO OTHER TEXT. STRICTLY JSON ONLY.

{{
  "passed": boolean,
  "score": number,
  "xp": number,
  "feedback": "encouraging feedback on their pitch delivery, acknowledging their effort"
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


# ============================================
# GROUP CHAT MESSAGING ENDPOINTS
# ============================================

def verify_token():
    """Helper to verify JWT and return user. Returns (user, error_response) tuple."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, (jsonify({'status': 'error', 'message': 'missing token'}), 401)
    token = auth.split(' ', 1)[1]
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return None, (jsonify({'status': 'error', 'message': 'invalid token'}), 401)

    user = users_col.find_one({'username': data.get('username')})
    if not user:
        return None, (jsonify({'status': 'error', 'message': 'user not found'}), 404)
    
    return user, None


@chat_bp.route('/post-message', methods=['POST'])
def post_message():
    """Post a message to a chat room.
    
    Request JSON:
    {
        "room_id": "room_id",
        "text": "message text",
        "image_url": "optional image URL"
    }
    """
    user, error = verify_token()
    if error:
        return error

    payload = request.get_json() or {}
    room_id = payload.get('room_id')
    text = payload.get('text', '').strip()
    image_url = payload.get('image_url', '')

    if not room_id or (not text and not image_url):
        return jsonify({'status': 'error', 'message': 'room_id and text or image_url required'}), 400

    # Check for harmful content
    has_harmful, found_words = contains_harmful_content(text)
    
    # Filter the message regardless
    filtered_text = filter_message(text) if text else ''
    
    message = {
        'room_id': room_id,
        'username': user['username'],
        'user_id': str(user.get('_id')),
        'text': filtered_text,
        'image_url': image_url,
        'has_harmful_content': has_harmful,
        'flagged_words': found_words or [],
        'reactions': {},  # emoji: [list of usernames who reacted]
        'timestamp': datetime.now(timezone.utc),
        'edited': False
    }
    
    result = chat_messages_col.insert_one(message)
    message['_id'] = str(result.inserted_id)
    
    return jsonify({
        'status': 'success',
        'message': message,
        'content_warning': 'This message contained unkind language and has been filtered.' if has_harmful else None
    })


@chat_bp.route('/get-messages', methods=['GET'])
def get_messages():
    """Get messages from a chat room.
    
    Query params:
    - room_id: required
    - limit: optional (default 50)
    - skip: optional (default 0)
    """
    user, error = verify_token()
    if error:
        return error

    room_id = request.args.get('room_id')
    limit = int(request.args.get('limit', 50))
    skip = int(request.args.get('skip', 0))
    
    if not room_id:
        return jsonify({'status': 'error', 'message': 'room_id required'}), 400
    
    # Get messages
    cursor = chat_messages_col.find({'room_id': room_id}) \
        .sort('timestamp', 1) \
        .skip(skip) \
        .limit(limit)
    
    messages = []
    for msg in cursor:
        msg['_id'] = str(msg['_id'])
        messages.append(msg)
    
    return jsonify({
        'status': 'success',
        'messages': messages,
        'count': len(messages)
    })


@chat_bp.route('/react', methods=['POST'])
def react_to_message():
    """React to a message with an emoji.
    
    Request JSON:
    {
        "message_id": "message_id",
        "emoji": "emoji string"
    }
    """
    user, error = verify_token()
    if error:
        return error

    payload = request.get_json() or {}
    message_id = payload.get('message_id')
    emoji = payload.get('emoji', '').strip()

    if not message_id or not emoji:
        return jsonify({'status': 'error', 'message': 'message_id and emoji required'}), 400

    try:
        msg = chat_messages_col.find_one({'_id': ObjectId(message_id)})
        if not msg:
            return jsonify({'status': 'error', 'message': 'message not found'}), 404
    except Exception:
        return jsonify({'status': 'error', 'message': 'invalid message_id'}), 400

    # Update reaction - add user to emoji list or remove if already reacted
    reactions = msg.get('reactions', {})
    if emoji not in reactions:
        reactions[emoji] = []
    
    username = user['username']
    if username in reactions[emoji]:
        # Remove reaction
        reactions[emoji].remove(username)
        if len(reactions[emoji]) == 0:
            del reactions[emoji]
    else:
        # Add reaction
        reactions[emoji].append(username)
    
    chat_messages_col.update_one(
        {'_id': ObjectId(message_id)},
        {'$set': {'reactions': reactions}}
    )
    
    return jsonify({
        'status': 'success',
        'reactions': reactions
    })


@chat_bp.route('/image-reactions', methods=['GET'])
def get_image_reactions():
    """Get all reactions for images in a room.
    
    Query params:
    - room_id: required
    """
    user, error = verify_token()
    if error:
        return error

    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({'status': 'error', 'message': 'room_id required'}), 400
    
    # Get all messages with images and their reactions
    cursor = chat_messages_col.find({
        'room_id': room_id,
        'image_url': {'$exists': True, '$ne': ''}
    }).sort('timestamp', 1)
    
    images = []
    for msg in cursor:
        msg['_id'] = str(msg['_id'])
        images.append({
            'message_id': msg['_id'],
            'username': msg['username'],
            'image_url': msg['image_url'],
            'text': msg.get('text', ''),
            'reactions': msg.get('reactions', {}),
            'timestamp': msg['timestamp']
        })
    
    return jsonify({
        'status': 'success',
        'images': images,
        'count': len(images)
    })

