"""Generate ElevenLabs audio files for the Emotion Matrix deck.

Usage:
    # install requirements (if not already)
    pip install -r backend/requirements.txt

    # Export your ElevenLabs API key
    set ELEVENLABS_API_KEY=your_key_here      (Windows PowerShell)
    $env:ELEVENLABS_API_KEY = 'your_key_here' (PowerShell session)

    # Run (dry-run prints actions without performing network calls)
    python scripts/generate_elevenlabs_audio.py --deck template/static/data/emotion-matrix-deck.json --outdir template/static/audio/elevenlabs --dry-run
    python scripts/generate_elevenlabs_audio.py --deck template/static/data/emotion-matrix-deck.json --outdir template/static/audio/elevenlabs

Notes:
- This script uses ElevenLabs Text-to-Speech HTTP API.
- Provide your `ELEVENLABS_API_KEY` in the environment.
- The default `voice_id` and voice settings can be adjusted below.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path

ELEVENLABS_ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Default voice id placeholder; replace with your preferred voice id from ElevenLabs dashboard
DEFAULT_VOICE_ID = "l4Coq6695JDX9xtLqXDE"

DEFAULT_STABILITY = 0.35
DEFAULT_SIMILARITY = 0.75


def load_deck(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def build_prompt(card):
    # Prefer an explicit 'audioPrompt' if present, otherwise use transcriptHint
    prompt = card.get('audioPrompt') or card.get('transcriptHint') or ''
    return prompt


def synthesize_text_to_mp3(api_key, voice_id, text, stability, similarity_boost):
    url = ELEVENLABS_ENDPOINT.format(voice_id=voice_id)
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    payload = {
        'text': text,
        'voice_settings': {
            'stability': stability,
            'similarity_boost': similarity_boost
        }
    }

    r = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
    r.raise_for_status()
    return r.content


def main():
    parser = argparse.ArgumentParser(description='Generate ElevenLabs audio for emotion matrix deck')
    parser.add_argument('--deck', required=True, help='Path to deck JSON')
    parser.add_argument('--outdir', default='template/static/audio/elevenlabs', help='Output directory for MP3s')
    parser.add_argument('--voice-id', default=DEFAULT_VOICE_ID, help='ElevenLabs voice id')
    parser.add_argument('--stability', type=float, default=DEFAULT_STABILITY)
    parser.add_argument('--similarity', type=float, default=DEFAULT_SIMILARITY)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    deck_path = Path(args.deck)
    outdir = Path(args.outdir)

    if not deck_path.exists():
        print('Deck file not found:', deck_path)
        sys.exit(1)

    data = load_deck(deck_path)
    cards = data.get('cards', [])

    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key and not args.dry_run:
        print('Missing ELEVENLABS_API_KEY environment variable. Aborting.')
        sys.exit(1)

    for card in cards:
        audio_src = card.get('audioSrc')
        if not audio_src:
            print('Card has no audioSrc, skipping:', card.get('id'))
            continue

        # audioSrc is like /static/audio/elevenlabs/001_passive_aggressive.mp3
        filename = Path(audio_src).name
        out_path = outdir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)

        prompt = build_prompt(card)
        if not prompt:
            print(f"Warning: card {card.get('id')} has no prompt. Skipping.")
            continue

        if out_path.exists():
            print(f"Skipping existing file: {out_path}")
            continue

        print(f"Generating: {out_path} — prompt: {prompt}")
        if args.dry_run:
            continue

        try:
            audio_bytes = synthesize_text_to_mp3(api_key, args.voice_id, prompt, args.stability, args.similarity)
            with open(out_path, 'wb') as fh:
                fh.write(audio_bytes)
            print('Saved:', out_path)
        except requests.exceptions.RequestException as e:
            print('Network error while generating audio for', card.get('id'), e)
        except Exception as e:
            print('Error while saving audio for', card.get('id'), e)


if __name__ == '__main__':
    main()
"""Generate ElevenLabs audio files for the Emotion Matrix deck.

Usage:
    # install requirements (if not already)
    pip install -r backend/requirements.txt

    # Export your ElevenLabs API key
    set ELEVENLABS_API_KEY=your_key_here      (Windows PowerShell)
    $env:ELEVENLABS_API_KEY = 'your_key_here' (PowerShell session)

    # Run (dry-run prints actions without performing network calls)
    python scripts/generate_elevenlabs_audio.py --deck template/static/data/emotion-matrix-deck.json --outdir template/static/audio/elevenlabs --dry-run
    python scripts/generate_elevenlabs_audio.py --deck template/static/data/emotion-matrix-deck.json --outdir template/static/audio/elevenlabs

Notes:
- This script uses ElevenLabs Text-to-Speech HTTP API.
- Provide your `ELEVENLABS_API_KEY` in the environment.
- The default `voice_id` and voice settings can be adjusted below.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path

ELEVENLABS_ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Default voice id placeholder; replace with your preferred voice id from ElevenLabs dashboard
DEFAULT_VOICE_ID = "your_voice_id_here"

DEFAULT_STABILITY = 0.35
DEFAULT_SIMILARITY = 0.75


def load_deck(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def build_prompt(card):
    # Prefer an explicit 'audioPrompt' if present, otherwise use transcriptHint
    prompt = card.get('audioPrompt') or card.get('transcriptHint') or ''
    # Add small heuristic modifiers if needed
    return prompt


def synthesize_text_to_mp3(api_key, voice_id, text, stability, similarity_boost):
    url = ELEVENLABS_ENDPOINT.format(voice_id=voice_id)
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    payload = {
        'text': text,
        'voice_settings': {
            'stability': stability,
            'similarity_boost': similarity_boost
        }
    }

    r = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
    r.raise_for_status()
    return r.content


def main():
    parser = argparse.ArgumentParser(description='Generate ElevenLabs audio for emotion matrix deck')
    parser.add_argument('--deck', required=True, help='Path to deck JSON')
    parser.add_argument('--outdir', default='template/static/audio/elevenlabs', help='Output directory for MP3s')
    parser.add_argument('--voice-id', default=DEFAULT_VOICE_ID, help='ElevenLabs voice id')
    parser.add_argument('--stability', type=float, default=DEFAULT_STABILITY)
    parser.add_argument('--similarity', type=float, default=DEFAULT_SIMILARITY)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    deck_path = Path(args.deck)
    outdir = Path(args.outdir)

    if not deck_path.exists():
        print('Deck file not found:', deck_path)
        sys.exit(1)

    data = load_deck(deck_path)
    cards = data.get('cards', [])

    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key and not args.dry_run:
        print('Missing ELEVENLABS_API_KEY environment variable. Aborting.')
        sys.exit(1)

    for card in cards:
        audio_src = card.get('audioSrc')
        if not audio_src:
            print('Card has no audioSrc, skipping:', card.get('id'))
            continue

        # audioSrc is like /static/audio/elevenlabs/001_passive_aggressive.mp3
        filename = Path(audio_src).name
        out_path = outdir / filename
        ensure_dir(out_path)

        prompt = build_prompt(card)
        if not prompt:
            print(f"Warning: card {card.get('id')} has no prompt. Skipping.")
            continue

        if out_path.exists():
            print(f"Skipping existing file: {out_path}")
            continue

        print(f"Generating: {out_path} — prompt: {prompt}")
        if args.dry_run:
            continue

        try:
            audio_bytes = synthesize_text_to_mp3(api_key, args.voice_id, prompt, args.stability, args.similarity)
            with open(out_path, 'wb') as fh:
                fh.write(audio_bytes)
            print('Saved:', out_path)
        except requests.exceptions.RequestException as e:
            print('Network error while generating audio for', card.get('id'), e)
        except Exception as e:
            print('Error while saving audio for', card.get('id'), e)


if __name__ == '__main__':
    main()
