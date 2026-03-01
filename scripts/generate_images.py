import os
import sys
import json
import argparse
import requests
import time
from pathlib import Path

def load_deck(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_image_prompt(card):
    options = card.get('options', [])
    correct_idx = card.get('correctAnswerIndex')
    emotion = options[correct_idx] if correct_idx is not None and correct_idx < len(options) else 'neutral'
    
    # Keep the prompt slightly simpler to avoid generation timeouts
    prompt = f"photorealistic portrait, face of a person showing {emotion} emotion, high quality, 4k"
    return prompt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deck', required=True)
    parser.add_argument('--outdir', default='template/static/images/faces')
    # Use 'turbo' as default because it is much more stable than 'flux'
    parser.add_argument('--model', default='turbo') 
    args = parser.parse_args()

    data = load_deck(args.deck)
    cards = data.get('cards', [])

    out_dir_path = Path(args.outdir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Mimic a real browser precisely
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    for card in cards:
        image_src = card.get('imageSrc')
        if not image_src: continue

        filename = Path(image_src).name
        out_path = out_dir_path / filename

        if out_path.exists():
            continue

        prompt_text = build_image_prompt(card)
        encoded_prompt = requests.utils.quote(prompt_text)
        
        # Using the standard image.pollinations.ai endpoint
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model={args.model}&seed={int(time.time())}"

        print(f"Requesting: {card.get('id')} ({prompt_text})...")

        max_retries = 3
        success = False

        for i in range(max_retries):
            try:
                # 60 second timeout for the AI to finish drawing
                response = requests.get(url, headers=headers, timeout=60)
                
                # VALIDATION 1: Check HTTP Status
                if response.status_code != 200:
                    print(f"  [Attempt {i+1}] Error {response.status_code}. Retrying...")
                    time.sleep(5)
                    continue

                # VALIDATION 2: Check if content is actually an image
                content_type = response.headers.get('Content-Type', '')
                if 'image' not in content_type:
                    print(f"  [Attempt {i+1}] Received text/HTML instead of an image. Server might be busy.")
                    time.sleep(5)
                    continue

                # VALIDATION 3: Check file size (Real images should be > 30KB)
                if len(response.content) < 5000:
                    print(f"  [Attempt {i+1}] File too small ({len(response.content)} bytes). Likely an error placeholder.")
                    time.sleep(5)
                    continue

                # If it passed all checks, save it
                with open(out_path, 'wb') as f:
                    f.write(response.content)
                print(f"  Successfully saved: {out_path} ({len(response.content)} bytes)")
                success = True
                break

            except Exception as e:
                print(f"  [Attempt {i+1}] Connection error: {e}")
                time.sleep(5)

        if not success:
            print(f"  !!! FAILED to get valid image for {card.get('id')} after {max_retries} tries.")
        
        # Wait 2 seconds between cards to avoid triggering rate limits
        time.sleep(2)

if __name__ == '__main__':
    main()