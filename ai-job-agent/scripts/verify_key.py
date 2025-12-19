import os
import requests
from openai import OpenAI

def verify_key(api_key, base_url, model_name):
    print(f"Testing key against: {base_url}")
    print(f"Model: {model_name}")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Hello, respond with 'Valid' if you can read this."}
            ],
            max_tokens=5
        )
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Test with OpenRouter since the key looks like an OpenRouter key
    key = "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"
    
    # Try OpenRouter
    or_url = "https://openrouter.ai/api/v1"
    or_model = "google/gemini-2.0-flash-exp:free" # Common free model on OpenRouter
    
    print("--- Testing OpenRouter ---")
    if verify_key(key, or_url, or_model):
        print("RESULT: Key is VALID for OpenRouter.")
    else:
        # Try Xiaomi
        xiaomi_url = "https://api.xiaomi.ai/v1"
        xiaomi_model = "MiMo-V2-Flash"
        print("\n--- Testing Xiaomi ---")
        if verify_key(key, xiaomi_url, xiaomi_model):
            print("RESULT: Key is VALID for Xiaomi.")
        else:
            print("RESULT: Key is INVALID or couldn't connect to either provider.")
