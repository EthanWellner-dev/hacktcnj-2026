"""Utility functions for AI, voice synthesis, and API response handling."""

import json
import re
import base64
import requests
from config import GEMINI_CLIENT, API_KEYS, HAS_ELEVENLABS


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


def call_ai_model(prompt, model='gemini', use_fallback=True):
    """
    Call Gemini models with fallback between different Gemini models.
    Attempts gemini-2.5-flash-lite first, then gemini-2.5-flash if rate limited.
    Returns (success, response_text, model_used)
    """
    models_to_try = [
        'gemini-2.5-flash-lite',
        'gemini-2.5-flash',
        'gemini-1.5-flash'
    ]
    
    if not GEMINI_CLIENT:
        return (False, None, None)
    
    for gemini_model in models_to_try:
        try:
            response = GEMINI_CLIENT.models.generate_content(
                model=gemini_model,
                contents=prompt
            )
            print(f"✓ AI call succeeded with {gemini_model}")
            return (True, response.text.strip(), gemini_model)
        except Exception as e:
            error_str = str(e).lower()
            if 'rate' in error_str or 'quota' in error_str or 'resource_exhausted' in error_str:
                print(f"⚠ {gemini_model} rate limited, trying next model: {e}")
                continue
            else:
                print(f"✗ {gemini_model} error: {e}")
                continue
    
    print("✗ All Gemini models exhausted/failed")
    return (False, None, None)


def get_voice_for_scenario(scenario):
    """
    Map scenario/persona to appropriate ElevenLabs voice ID.
    Different scenarios should have different voice characteristics.
    """
    voice_map = {
        'angry_boss': 'jBpfuIE2acCO8z3wKNLl',  # Marcus - professional male, assertive
        'concerned_boss': 'EXAVITQu4EJ3m4xKqAda',  # Grace - professional female, empathetic
        'frustrated_colleague': 'jBpfuIE2acCO8z3wKNLl',  # Marcus - male colleague
        'dynamic': 'jBpfuIE2acCO8z3wKNLl',  # Default to Marcus
        'default': 'jBpfuIE2acCO8z3wKNLl'
    }
    return voice_map.get(scenario, voice_map['default'])


def synthesize_voice(text, elevenlabs_key, scenario='default'):
    """
    Synthesize text to speech using ElevenLabs API with persona-matched voice.
    Returns a URL to the synthesized audio or None if it fails.
    """
    try:
        voice_id = get_voice_for_scenario(scenario)
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "xi-api-key": elevenlabs_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.85
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            # For hackathon purposes, encode audio as data URI
            audio_b64 = base64.b64encode(response.content).decode('utf-8')
            return f"data:audio/mpeg;base64,{audio_b64}"
        else:
            print(f"ElevenLabs error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"ElevenLabs synthesis error: {e}")
        return None
