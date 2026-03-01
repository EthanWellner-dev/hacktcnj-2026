from flask import Blueprint, render_template, request, jsonify, current_app
from config import API_KEYS
from utils import synthesize_voice

module8_bp = Blueprint('module8', __name__, template_folder='../template')

# Hardcoded scenario texts - full scripts to be read by ElevenLabs (30 sec / ~50 words each)
SCENARIOS = [
    "You know, I've been really into vintage typewriters lately. I have about forty-seven of them now. The 1952 Royal Quiet Portables are especially fascinating—their ribbon mechanism is unique. I catalog each one by serial number. The mechanical differences between batches are quite extraordinary. Isn't that incredible?",
    
    "I wanted to give you feedback on your work. Your presentation showed effort, but the execution fell short. The structure was scattered, the data visualization wasn't clear, and some conclusions didn't match your evidence. You have potential, but you need to refocus and be more deliberate about your approach.",
    
    "Alright class, I've got a good joke for you. Why did the biology student break up with the chemistry student? Because there was no real chemistry! Get it? No chemistry? *awkward silence* Okay then, nobody? Let's continue with chapter seven.",
    
    "Looking at last quarter's metrics, cell A-twenty-four shows a point-three-seven percent increase. Notice column D through G here—the variance calculations are quite complex. Let me zoom in so you can see the decimal precision. Yes, this detail matters. Very important. Now look at the trend line.",
    
    "Oh no, I'm so sorry! I wasn't paying attention and I knocked over my coffee. It's getting dangerously close to your laptop! Quick, can you move it? Do you have paper towels? I feel terrible about this. I wasn't being careful. I'm really, really sorry.",
    
    "Oh wow, thank you so much! This is really thoughtful. *unwrapping sounds* A book about knitting. That's so... unique. I really appreciate you thinking of me. This is definitely something special. You're so generous. Thank you so much for this gift!",
    
    "*Elevator dings, doors close* Good morning. *long awkward silence* *stares ahead* The elevator hums. *more silence* *floor counter beeps* Nobody says anything. Another beep. The air is heavy. *more silence* *doors slowly open*",
    
    "Hey, good to see you! How's it going? Oh, by the way, how's everything with you, James? Wait, I mean... James, right? Yeah, I'm pretty sure it's James. Definitely James. How are you doing, James? That's your name, isn't it?",
    
    "Okay everyone, gather a bit closer. No wait, move left. Actually, move right. Hmm, wait. My camera isn't focusing correctly. Let me adjust. The settings are acting weird. This lens isn't cooperating. Okay, stay right there. Almost have it. Just one more second. Hold still please.",
    
    "You never listen to me! You always do exactly what you want! I can't believe you! Oh please, YOU'RE the one who never compromises! Don't blame me! You're being completely unreasonable! This is ridiculous! I can't take this anymore! You're insufferable!",
    
    "*LOUD CRASH* *BANG* Oh my gosh! *heavy book hits floor* I dropped my textbook! *rustling of papers* Everything fell everywhere. Papers everywhere. *papers shuffling* So embarrassing. *awkward pause* Sorry about that.",
    
    "So anyway, like I was saying, the colonoscopy was super uncomfortable. The doctor said my intestines weren't in ideal condition. And then the worst part was, well, they found something. Nothing serious, but still concerning. And afterwards I had digestive issues for three weeks straight.",
    
    "In case of loss of cabin pressure, oxygen masks will automatically deploy. Place the mask over your nose and mouth, secure the elastic band, and breathe normally. If traveling with a child, secure your mask first. Keep your seatbelt fastened. Review the safety card in your seat pocket.",
    
    "So as you can see on the screen, the quarterly results are... wait, the presentation's frozen. Just give me a moment. It's loading. I know this is awkward. Still loading. Come on. This never happens. Let me restart. Any second now. You're all patient.",
    
    "So, uh, what do you do? Oh, that's cool. Yeah. *long silence* So do you come to these events often? That's nice. *more silence* Yeah, the snacks are good. They have snacks here. *uncomfortable pause* Right. Well... yeah.",
    
    "Hi, thanks for checking in. The doctor is running about twenty minutes behind schedule today. I apologize. Please have a seat in the waiting room. Help yourself to water. It shouldn't be too long. Well, maybe thirty minutes. We'll call you when they're ready.",
    
    "Did you see the email? Mark meant to reply privately but hit Reply All instead. He said, 'This project is a waste and Sarah doesn't know what she's doing.' Thirty-seven people got it. Mark's hiding in his office. Everyone's reading it now. This is so embarrassing.",
    
    "Excuse me, I bought this shirt three weeks ago and the seam came apart. I want a refund. This quality is unacceptable. What are you going to do about it? So there's nothing you can do? That's ridiculous. I want a manager. This is terrible service."
]


@module8_bp.route('/module8')
def module8_page():
    return render_template('module8.html')


@module8_bp.route('/module8/audio/<int:idx>')
def module8_audio(idx: int):
    """Synthesize audio for a scenario using ElevenLabs API."""
    idx = max(0, min(idx, len(SCENARIOS) - 1))
    text = SCENARIOS[idx]
    
    # Get ElevenLabs API key
    elevenlabs_key = API_KEYS.get('elevenlabs')
    if not elevenlabs_key:
        current_app.logger.error('ElevenLabs API key not configured')
        return jsonify({
            'error': 'audio_generation_failed',
            'message': 'ElevenLabs API key not configured'
        }), 500
    
    try:
        # Synthesize audio using ElevenLabs
        audio_url = synthesize_voice(text, elevenlabs_key, scenario='dynamic')
        
        if not audio_url:
            current_app.logger.error('Failed to synthesize audio for scenario %d', idx)
            return jsonify({
                'error': 'audio_generation_failed',
                'message': 'Could not synthesize audio'
            }), 500
        
        return jsonify({'url': audio_url}), 200
    except Exception as e:
        current_app.logger.exception('Audio synthesis error: %s', e)
        return jsonify({
            'error': 'audio_generation_failed',
            'message': 'Server error generating audio'
        }), 500


@module8_bp.route('/module8/result', methods=['POST'])
def module8_result():
    data = request.get_json() or {}
    current_app.logger.info('Module8 result: %s', data)
    
    accuracy_score = data.get('accuracy_score', 0)
    xp_earned = data.get('xp', 0)
    
    # TODO: In a real app, you would:
    # 1. Get the current user from the token
    # 2. Update their XP in the database
    # 3. Log this challenge result
    
    # For now, just return the XP amount
    # The frontend will have already calculated it based on accuracy
    return jsonify({
        'status': 'ok',
        'xp_earned': xp_earned,
        'accuracy_score': accuracy_score,
        'xp_current': data.get('xp', 0)  # This would come from DB in production
    }), 200
