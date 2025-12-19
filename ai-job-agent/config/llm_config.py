import os

# API Configuration for Xiaomi MiMo-V2-Flash
# The user should provide these via environment variables
XIAOMI_API_KEY = os.getenv("XIAOMI_API_KEY", "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")
# Default to a placeholder if not set, user needs to override this if their provider is different
XIAOMI_BASE_URL = os.getenv("XIAOMI_BASE_URL", "https://api.xiaomi.ai/v1") 

# Model Name (Updated for OpenRouter)
MODEL_NAME = "google/gemini-2.0-flash-exp:free"
