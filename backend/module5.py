"""Module 5 (Conflict Resolution) routes - tone checking and scenario generation."""

from flask import Blueprint, request, jsonify
import jwt
import json
import tempfile
import os as os_cleanup
from datetime import datetime, timezone
from config import users_col, training_col, JWT_SECRET, JWT_ALGO, GEMINI_CLIENT, API_KEYS, HAS_ELEVENLABS
from utils import extract_json_from_response, call_ai_model, synthesize_voice

module5_bp = Blueprint('module5', __name__, url_prefix='/api/module5')


@module5_bp.route('/tone-check', methods=['POST'])
def tone_check():
    """
    Evaluate user's audio response in a conflict scenario using Gemini's native audio capabilities.
    
    Request: 
    - multipart/form-data with 'audio' file field
    - Requires Bearer token
    
    Response: JSON with score, tone, feedback, next_dialogue (text), and synthesized audio
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

    # Check XP gate (5000+)
    user_xp = user.get('xp', 0)
    if user_xp < 5000:
        return jsonify({
            'status': 'locked',
            'message': f'Module 5 requires 5000 XP to unlock. You have {user_xp} XP.',
            'xp_required': 5000,
            'xp_current': user_xp
        }), 403

    # Extract audio file from request
    if 'audio' not in request.files:
        return jsonify({'status': 'error', 'message': 'no audio file provided'}), 400

    audio_file = request.files['audio']
    audio_blob = audio_file.read()
    
    if not audio_blob:
        return jsonify({'status': 'error', 'message': 'empty audio file'}), 400

    scenario = request.form.get('scenario', 'angry_boss')
    context = request.form.get('context', '')

    # System prompt for Gemini to evaluate tone and respond as the boss
    system_prompt = """You are Sarah, an angry manager. You are evaluating your employee's response to your hostile message. This is practice for neurodiveragent individuals to improve their social skills. Analyze their response based on the following criteria:
Listen carefully to the audio provided. Analyze their:
1. Firmness - Did they set a boundary?
2. Vocal Tone - Did they sound calm, anxious, defensive, or professional?
3. Emotional Control - Did they respond appropriately without escalating?
4. Professionalism - Did they maintain composure?

Return ONLY valid JSON. NO OTHER TEXT. STRICTLY JSON ONLY:
{
  "score": <50-100>,
  "detected_tone": "<e.g., Calm, Shaky, Defensive, Professional, Anxious>",
  "professionalism": <50-100>,
  "boundary_setting": <50-100>,
  "vocal_composure": <50-100>,
  "feedback": "<Brief critique of their response and vocal delivery>",
  "next_dialogue": "<David's verbal response to what they just said. Keep it 1-2 sentences>",
  "is_resolved": <boolean>,
  "is_escalating": <boolean>
}"""

    # Determine MIME type (assumes webm or mp4)
    audio_mime = 'audio/webm'
    if audio_file.filename and audio_file.filename.endswith('.mp4'):
        audio_mime = 'audio/mp4'

    try:
        # Upload audio file to Gemini using the File API
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(audio_blob)
            tmp_path = tmp.name
        
        try:
            # Upload the file directly via its temporary path
            uploaded_file = GEMINI_CLIENT.files.upload(
                file=tmp_path,
                config={
                    'mime_type': audio_mime,
                    'display_name': audio_file.filename
                }
            )            
            # Call Gemini with the uploaded file
            response = GEMINI_CLIENT.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[
                    system_prompt,
                    uploaded_file
                ]
            )
        finally:
            # Clean up temp file
            try:
                if os_cleanup.path.exists(tmp_path):
                    os_cleanup.remove(tmp_path)
            except:
                pass
        
        response_text = response.text.strip()
        result = extract_json_from_response(response_text)
        
        # Extract dialogue for TTS
        next_dialogue = result.get('next_dialogue', "")
        xp_gain = int(result.get('score', 50) / 10)  # Convert score to XP (max 10)
        xp_gain = max(5, min(100, xp_gain))  # Clamp between 5-100
        
        # Synthesize audio response using ElevenLabs (boss responding)
        audio_url = None
        if HAS_ELEVENLABS and API_KEYS['elevenlabs'] and next_dialogue:
            try:
                audio_url = synthesize_voice(next_dialogue, API_KEYS['elevenlabs'], scenario='dynamic')
            except Exception as e:
                print(f"⚠ ElevenLabs synthesis failed: {e}")
                # Continue without audio if synthesis fails
        
        # Update user XP
        users_col.update_one({'username': user['username']}, {'$inc': {'xp': xp_gain}})
        updated_user = users_col.find_one({'username': user['username']})
        
        # Record training result
        record = {
            'username': user['username'],
            'module': 'module5_tone_check',
            'scenario': scenario,
            'results': {
                'score': result.get('score', 0),
                'detected_tone': result.get('detected_tone', ''),
                'professionalism': result.get('professionalism', 0),
                'boundary_setting': result.get('boundary_setting', 0),
                'vocal_composure': result.get('vocal_composure', 0),
                'is_resolved': result.get('is_resolved', False),
                'is_escalating': result.get('is_escalating', False)
            },
            'xp_awarded': xp_gain,
            'timestamp': datetime.now(timezone.utc)
        }
        training_col.insert_one(record)
        
        return jsonify({
            'status': 'success',
            'score': result.get('score', 0),
            'detected_tone': result.get('detected_tone', ''),
            'professionalism': result.get('professionalism', 0),
            'boundary_setting': result.get('boundary_setting', 0),
            'vocal_composure': result.get('vocal_composure', 0),
            'feedback': result.get('feedback', ''),
            'next_dialogue': next_dialogue,
            'audio_url': audio_url,
            'is_resolved': result.get('is_resolved', False),
            'is_escalating': result.get('is_escalating', False),
            'xp_awarded': xp_gain,
            'xp_current': updated_user.get('xp', 0)
        })
        
    except json.JSONDecodeError as je:
        print(f"JSON parse error: {je}")
        return jsonify({'status': 'error', 'message': 'failed to parse AI response'}), 500
    except Exception as e:
        print(f"Error in tone-check: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@module5_bp.route('/generate-scenario', methods=['POST'])
def generate_scenario():
    """
    Generate a dynamic conflict scenario using Gemini and synthesize it to audio using ElevenLabs.
    Returns the scenario text and a data URI of the synthesized audio.
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

    # Check XP gate
    user_xp = user.get('xp', 0)
    if user_xp < 5000:
        return jsonify({
            'status': 'locked',
            'message': f'Module 5 requires 5000 XP to unlock. You have {user_xp} XP.',
            'xp_required': 5000,
            'xp_current': user_xp
        }), 403

    if not GEMINI_CLIENT:
        return jsonify({'status': 'error', 'message': 'AI not configured'}), 500

    # Prompt Gemini to generate a realistic, varied conflict scenario
    scenario_prompt = """Generate ONE realistic workplace conflict scenario as if you are an upset manager speaking to your employee.

Requirements:
1. Make it 1-2 sentences, emotionally charged but professional
2. The scenario should be realistic (deadline pressure, quality issues, communication breakdown, etc.)
3. Sound like a real manager - direct, frustrated, but not abusive
4. Vary from common scenarios (don't repeat "I needed this report yesterday" exactly)

Return ONLY the dialogue string (no JSON, no quotes, just the raw text):"""

    try:
        success, response_text, model_used = call_ai_model(scenario_prompt)
        
        if not success or not response_text:
            return jsonify({'status': 'error', 'message': 'failed to generate scenario'}), 500
        
        scenario_text = response_text.strip()
        
        # Synthesize the scenario to speech using ElevenLabs
        audio_url = None
        if HAS_ELEVENLABS and API_KEYS['elevenlabs']:
            try:
                audio_url = synthesize_voice(scenario_text, API_KEYS['elevenlabs'], scenario='dynamic')
            except Exception as e:
                print(f"⚠ ElevenLabs synthesis failed: {e}")
                # Continue without audio if synthesis fails
        
        return jsonify({
            'status': 'success',
            'scenario_text': scenario_text,
            'audio_url': audio_url,
            'model_used': model_used
        })
        
    except Exception as e:
        print(f"Error generating scenario: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
