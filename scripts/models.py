import os
import sys
from google import genai

def list_available_models():
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print(f"{'MODEL NAME':<45} | {'ACTIONS'}")
    print("-" * 90)

    try:
        # Use the list method which returns a generator of Model objects
        for model in client.models.list():
            # In the new SDK, the attribute is 'supported_actions'
            actions = model.supported_actions or []
            
            # Clean up name for display
            display_name = model.name
            
            # Identify if it's an image model
            # Usually contains 'generateImages' in actions or 'imagen' in name
            is_image = "generate_images" in [a.lower() for a in actions] or "imagen" in display_name.lower()
            star = " [IMAGE MODEL] ★" if is_image else ""
            
            print(f"{display_name:<45} | {', '.join(actions)}{star}")

    except Exception as e:
        print(f"Error fetching models: {e}")
        print("\nNote: If the list is empty or fails, your API key may not have permissions to list models.")

if __name__ == "__main__":
    list_available_models()