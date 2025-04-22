# utils.py
import os
import sys
import tempfile

import pyautogui

import config  # Import our config constants


def take_screenshot():
    """Takes a screenshot and saves it to a temporary file."""
    try:
        screenshot = pyautogui.screenshot()
        print("\nScreenshot taken.")

        # Create a temporary file securely
        with tempfile.NamedTemporaryFile(
            suffix=config.SCREENSHOT_TEMP_SUFFIX, delete=False
        ) as temp_file:
            screenshot_path = temp_file.name
            screenshot.save(screenshot_path)

        print(f"Screenshot saved temporarily to: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"\nError taking screenshot: {e}")
        if sys.platform == "linux":
            print("On Linux, ensure 'scrot' or 'gnome-screenshot' is installed.")
        elif sys.platform == "darwin":
            print("On macOS, ensure Screen Recording permission is granted.")
        return None


def cleanup_file(file_path):
    """Safely removes a file if it exists."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Temporary file deleted: {file_path}")
        except Exception as e:
            print(f"Warning: Could not delete temporary file {file_path}: {e}")
