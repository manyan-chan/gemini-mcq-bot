# config.py
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- General Configuration ---
# Hotkey format for pynput parsing
TRIGGER_HOTKEY_SCREENSHOT = "shift+space"
TRIGGER_HOTKEY_TEXT = "command+c"
EXIT_HOTKEY_STR = "esc"

# --- Gemini Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17"  # Or your preferred vision model

GEMINI_INSTRUCTION_PROMPT = """Analyze the following content.
Identify any explicit question asked within the text.
Do not read out the question or any other text from the input.
If the question is a multiple-choice question, provide the correct option number or letter followed by 'is correct'. Example: Option 1 is correct.
Otherwise, provide the answer to the question concisely, without explaining the reasoning.
If no specific question is found, provide a brief summary of the text's main topic.
Do not add conversational filler like "Okay" or "Here is the analysis". Go straight to the answer or summary."""

# --- ElevenLabs Configuration ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "kPzsL2i3teMYv0FxEYQ6"
ELEVENLABS_MODEL = "eleven_turbo_v2_5"

# --- Screenshot Configuration ---
SCREENSHOT_TEMP_SUFFIX = ".png"

# --- Error Messages ---
ERROR_PREFIX = "Error:"
BLOCKED_PREFIX = "Blocked"

# --- Validation ---
REQUIRED_ENV_VARS = ["GOOGLE_API_KEY", "ELEVENLABS_API_KEY"]


def validate_config():
    """Checks if required API keys are present."""
    missing_keys = [var for var in REQUIRED_ENV_VARS if not globals().get(var)]
    if missing_keys:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_keys)}"
        )
        print("Please ensure they are set in your .env file.")
        return False
    return True
