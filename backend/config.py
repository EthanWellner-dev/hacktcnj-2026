"""Configuration module for Flask app - database, API keys, and constants."""

import os
from pymongo import MongoClient
from datetime import timedelta

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

# ElevenLabs for voice synthesis
try:
    import requests
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False
    print("Warning: requests not installed. Install with: pip install requests")

# Database configuration
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://etwellner_db_user:J6pk1WJJJeB4lvt5@init.4uvaz3g.mongodb.net/')
client = MongoClient(MONGO_URI)
db = client.social_sandbox
users_col = db.users
training_col = db.training_results

# JWT config
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-minimum-32-bytes-long-987654')
JWT_ALGO = 'HS256'

# Conversation starters for variety
CONVERSATION_STARTERS = [
    "That movie was actually wild, I didn't expect that ending.",
    "Have you seen any good movies lately?",
    "I just finished this show and it blew my mind.",
    "What's your take on good storytelling in films?",
    "I'm always looking for recommendations on what to watch next."
]


def load_api_keys():
    """Load API keys from secrets.env file."""
    secrets_path = os.path.join(os.path.dirname(__file__), 'secrets.env')
    keys = {
        'gemini': None,
        'elevenlabs': None
    }
    if not os.path.exists(secrets_path):
        return keys
    try:
        with open(secrets_path, 'r') as f:
            for line in f:
                if line.startswith('Gemini_Api_Key='):
                    keys['gemini'] = line.split('=', 1)[1].strip()
                elif line.startswith('ElevenLabs_Api_Key='):
                    keys['elevenlabs'] = line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error loading API keys: {e}")
    return keys


API_KEYS = load_api_keys()

# Initialize Gemini client
GEMINI_CLIENT = None
if API_KEYS['gemini']:
    try:
        GEMINI_CLIENT = genai.Client(api_key=API_KEYS['gemini'])
        print("✓ Gemini API initialized with fallback support")
    except Exception as e:
        print(f"✗ Failed to initialize Gemini client: {e}")
else:
    print("✗ Gemini API key not found in secrets.env")
