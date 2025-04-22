# Gemini Hotkey Assistant (Screenshot & Text Analysis)


This application allows you to instantly analyze the content of your screen (via screenshot) or your clipboard text using Google's Gemini AI models. Simply press a configurable hotkey, and the application will:

1.  **Capture:** Either take a screenshot or grab the text from your clipboard.
2.  **Analyze:** Send the captured content to the Gemini API with a specific instruction prompt (e.g., answer a question found in the content, summarize).
3.  **Respond:** Print the analysis result to the console and optionally speak it aloud using ElevenLabs Text-to-Speech (TTS).

It provides two modes of operation via separate entry points:

*   `main_screenshot.py`: Analyzes screenshots.
*   `main_text.py`: Analyzes clipboard text.

## Features

*   **Hotkey Triggered:** Activate analysis instantly with keyboard shortcuts.
*   **Screenshot Analysis:** Captures the entire screen for visual analysis.
*   **Clipboard Text Analysis:** Grabs text content directly from the clipboard.
*   **Google Gemini Integration:** Leverages powerful multimodal (vision/text) AI for analysis.
*   **Customizable Analysis Prompt:** Tailor the `GEMINI_INSTRUCTION_PROMPT` in `config.py` to guide the AI's analysis (e.g., focus on summarization, question answering, specific data extraction).
*   **ElevenLabs TTS Output (Optional):** Get audible feedback of the analysis results.
*   **Configurable:** Easily change hotkeys, Gemini model, ElevenLabs voice/model, and API keys via configuration files.
*   **Graceful Exit:** Stop the listener cleanly using an exit hotkey.
*   **Error Handling:** Provides informative messages for common issues (API keys, blocked responses, etc.).

## Requirements

*   **Python:** 3.9 or higher recommended.
*   **API Keys:**
    *   **Google AI API Key:** For accessing Gemini models. Get one from [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   **ElevenLabs API Key (Optional):** If you want Text-to-Speech output. Get one from [ElevenLabs](https://elevenlabs.io/).
*   **Operating System Specific Dependencies:**
    *   **Linux:**
        *   Screenshot: `scrot` (recommended) or `gnome-screenshot`. Install via package manager (e.g., `sudo apt install scrot`).
        *   Clipboard: `xclip` or `xsel`. Install via package manager (e.g., `sudo apt install xclip`).
        *   Permissions: May require running as root or adding your user to the `input` group for global hotkey listening, depending on your display server setup (X11/Wayland).
    *   **macOS:**
        *   Permissions: Requires granting "Accessibility" and potentially "Input Monitoring" and "Screen Recording" permissions to your Terminal or Python executable in System Settings > Privacy & Security.
    *   **Windows:**
        *   Should generally work without extra OS dependencies for core features.

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/manyan-chan/gemini-mcq-bot.git
    cd gemini-mcq-bot
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate it:
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install OS-Specific Dependencies:**
    *   Install `scrot`/`gnome-screenshot` and `xclip`/`xsel` if you are on Linux.


## Configuration

1.  **Create `.env` file:**
    Rename or copy the `.env.example` file (if provided) or create a new file named `.env` in the root directory.

2.  **Add API Keys to `.env`:**
    ```dotenv
    # .env
    GOOGLE_API_KEY="YOUR_GOOGLE_AI_API_KEY_HERE"
    ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY_HERE" # Leave blank or remove if not using TTS
    ```
    Replace the placeholder values with your actual API keys.

3.  **Review `config.py` (Optional):**
    You can customize various settings directly in `config.py`:
    *   `TRIGGER_HOTKEY_SCREENSHOT`: Hotkey to trigger screenshot analysis (default: `shift+space`).
    *   `TRIGGER_HOTKEY_TEXT`: Hotkey to trigger clipboard analysis (default: `command+c`).
    *   `EXIT_HOTKEY_STR`: Hotkey to stop the application (default: `esc`).
    *   `GEMINI_MODEL_NAME`: The specific Gemini model to use.
    *   `GEMINI_INSTRUCTION_PROMPT`: The core instructions given to Gemini for analysis. **Modify this carefully to change the AI's behavior.**
    *   `ELEVENLABS_VOICE_ID`: The specific ElevenLabs voice to use for TTS.
    *   `ELEVENLABS_MODEL`: The specific ElevenLabs model to use for TTS.
    *   `ERROR_PREFIX`, `BLOCKED_PREFIX`: Prefixes for console output messages.

    **Note:** Ensure your hotkey strings use the correct key names recognized by `pynput` (see `hotkey_listener.py` `_KEY_MAP` or `pynput` documentation). Common modifiers are `shift`, `ctrl`, `alt`, `cmd` (or `command` on macOS).

## Usage

1.  **Activate Virtual Environment:** Make sure your virtual environment is active (`source venv/bin/activate` or `.\venv\Scripts\activate`).

2.  **Choose Your Mode and Run:**
    *   **For Screenshot Analysis:**
        ```bash
        python main_screenshot.py
        ```
    *   **For Clipboard Text Analysis:**
        ```bash
        python main_text.py
        ```

    **Important:** Run only *one* of these scripts at a time, unless you have configured unique trigger hotkeys for each in `config.py`.

3.  **Trigger Analysis:**
    *   **Screenshot Mode:** Press the `TRIGGER_HOTKEY_SCREENSHOT` (default: `Shift+Space`). The application will take a screenshot, analyze it, and provide the result.
    *   **Text Mode:** First, **copy** the text you want to analyze to your clipboard (e.g., using `Ctrl+C` or `Cmd+C`). Then, press the `TRIGGER_HOTKEY_TEXT` (default: `Cmd+C` - **be mindful if this overlaps with your system's copy command! Consider changing it in `config.py`**). The application will grab the clipboard text, analyze it, and provide the result.

4.  **Listen/Read Output:**
    *   The analysis result will be printed to the console.
    *   If ElevenLabs is configured and enabled, the result will also be spoken aloud.

5.  **Exit:**
    *   Press the `EXIT_HOTKEY_STR` (default: `Esc`) to stop the listener and exit the application gracefully.
    *   You can also use `Ctrl+C` in the terminal, which will be caught by the signal handler for a clean shutdown.

## Troubleshooting

*   **API Key Errors:** Ensure your `.env` file exists, is correctly formatted, and contains valid API keys. Check for typos.
*   **Module Not Found Errors:** Make sure you have installed all packages from `requirements.txt` within your activated virtual environment.
*   **Hotkey Not Working (macOS):** Grant Accessibility, Input Monitoring, and Screen Recording permissions in System Settings > Privacy & Security. You might need to grant them specifically to your terminal application or the Python executable. Restart the script after changing permissions.
*   **Hotkey Not Working (Linux):** Permissions issues are common. Try running with `sudo` (use caution!) or investigate adding your user to the `input` group. Wayland might have different requirements than X11.
*   **Screenshot Failed (Linux):** Ensure `scrot` or `gnome-screenshot` is installed.
*   **Clipboard Access Failed (Linux):** Ensure `xclip` or `xsel` is installed and working. May fail in headless environments.
*   **ElevenLabs TTS Failure:** Double-check your `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` / `ELEVENLABS_MODEL` in `config.py`. Check your character quota on the ElevenLabs website.
*   **Gemini "Blocked" Response:** The input (image or text) likely triggered Google's safety filters. Try with different content. Check the `BLOCKED_PREFIX` reason printed in the console.
*   **Incorrect Analysis:** Modify the `GEMINI_INSTRUCTION_PROMPT` in `config.py` to be more specific about the desired output. Experiment with different phrasing.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs, feature requests, or improvements.