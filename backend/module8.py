from flask import Blueprint, render_template, request, jsonify, current_app
import os
import subprocess
import shlex
import sys

module8_bp = Blueprint('module8', __name__, template_folder='../template')

# Hardcoded scenario texts mirrored on frontend indices
SCENARIOS = [
    "A coworker explains a long weekend getaway slideshow.",
    "A peer makes a backhanded compliment.",
    "The CEO tells a joke that falls flat.",
    "Someone loudly describes their diet plan.",
    "A colleague brags about an overblown achievement.",
    "A teammate recounts a tedious debugging story.",
    "A person shares an awkward dating anecdote.",
    "An office rival subtly takes credit for your idea.",
    "A client nitpicks minor layout details.",
    "A manager explains an irrelevant corporate process.",
    "A coworker asks for weekend favors repeatedly.",
    "Someone describes an uncomfortable medical procedure.",
    "A colleague complains about traffic in great detail.",
    "A team member rehashes last quarter's mistakes.",
    "A peer criticizes your preferred tooling choice.",
    "A vendor gives a longwinded sales pitch.",
    "A teammate tells a mildly offensive joke.",
    "A manager gives enthusiastic but vague praise.",
    "Someone recounts an embarrassing childhood story.",
    "A co-worker insists on telling a dream they had."
]


@module8_bp.route('/module8')
def module8_page():
    return render_template('module8.html')


def generate_audio_file(text: str, out_path: str) -> bool:
    """Try to generate an audio file by invoking the project's script.
    Falls back to returning False if generation cannot be performed."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate_elevenlabs_audio.py')
        script_path = os.path.normpath(script_path)
        cmd = [sys.executable, script_path, '--text', text, '--out', out_path]
        # Ensure output dir exists
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        current_app.logger.debug('Audio generation stdout: %s', proc.stdout)
        current_app.logger.debug('Audio generation stderr: %s', proc.stderr)
        return proc.returncode == 0 and os.path.exists(out_path)
    except Exception as e:
        current_app.logger.exception('Audio generation failed: %s', e)
        return False


@module8_bp.route('/module8/audio/<int:idx>')
def module8_audio(idx: int):
    idx = max(0, min(idx, len(SCENARIOS) - 1))
    text = SCENARIOS[idx]
    filename = f'module8_{idx}.mp3'
    out_rel = os.path.join('audio', 'elevenlabs', filename)
    out_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'template', 'static', out_rel))

    if not os.path.exists(out_path):
        ok = generate_audio_file(text, out_path)
        if not ok:
            # Generation didn't work; return JSON with fallback message
            return jsonify({'error': 'audio_generation_failed', 'message': 'Server could not generate audio.'}), 500

    return jsonify({'url': f'/static/{out_rel.replace('\\\\', '/')}'}), 200


@module8_bp.route('/module8/result', methods=['POST'])
def module8_result():
    data = request.get_json() or {}
    current_app.logger.info('Module8 result: %s', data)
    # In a real app we'd persist to DB. For now respond OK.
    return jsonify({'status': 'ok'}), 200
