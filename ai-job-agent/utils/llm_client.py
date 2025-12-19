import logging
import json
from openai import OpenAI
from config.llm_config import XIAOMI_API_KEY, XIAOMI_BASE_URL, MODEL_NAME

class LLMClient:
    """
    Wrapper for interacting with Xiaomi MiMo-V2-Flash model via OpenAI-compatible API.
    """
    def __init__(self):
        self.logger = logging.getLogger("LLMClient")
        
        if not XIAOMI_API_KEY:
            self.logger.warning("XIAOMI_API_KEY not found in environment variables.")
            
        self.client = OpenAI(
            api_key=XIAOMI_API_KEY if XIAOMI_API_KEY else "dummy_key", # Prevent immediate crash if key missing, but warn
            base_url=XIAOMI_BASE_URL
        )
        self.model = MODEL_NAME

    def generate_response(self, prompt, system_prompt="You are a helpful assistant."):
        """
        Generates a response from the model.
        Returns the content string.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # Low temperature for more deterministic scoring
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Failed to generate LLM response: {e}")
            return None
