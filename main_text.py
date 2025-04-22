# main_text.py
import signal
import sys
import time
import traceback  # Import traceback for detailed error logging

import pyperclip  # Import the clipboard library

# Import our modules
import config

# We don't need utils for taking/cleaning screenshots anymore
# import utils
from gemini_analyzer import GeminiAnalyzer
from hotkey_listener import HotkeyListener
from tts_speaker import ElevenLabsSpeaker


class TextAnalyzerApp:
    """
    Orchestrates the clipboard text analysis application using injected dependencies.
    """

    def __init__(
        self,
        speaker: ElevenLabsSpeaker | None,
        analyzer: GeminiAnalyzer,
        listener: HotkeyListener,
    ):
        """
        Initializes the application with injected dependencies.
        """
        self.speaker = speaker
        self.analyzer = analyzer
        self.listener = listener
        # Initialization messages handled by the creators or kept minimal

    def _get_clipboard_text(self) -> str | None:
        """Safely retrieves text content from the clipboard."""
        try:
            text = pyperclip.paste()
            if isinstance(text, str) and text.strip():
                print("\nClipboard text retrieved.")
                # Optional: Limit length if needed for API or performance
                # max_len = 10000
                # if len(text) > max_len:
                #     print(f"Warning: Clipboard text truncated to {max_len} characters.")
                #     return text[:max_len]
                return text
            elif isinstance(text, str):
                print("Clipboard contains empty string or only whitespace.")
                return None
            else:
                print("Clipboard does not contain text.")
                return None
        except pyperclip.PyperclipException as e:
            # Specific errors from pyperclip (e.g., on headless Linux without display)
            print(f"{config.ERROR_PREFIX} Failed to access clipboard: {e}")
            print(
                "Hint: Ensure clipboard utilities (like xclip/xsel on Linux) are installed."
            )
            return None
        except Exception as e:
            print(
                f"{config.ERROR_PREFIX} An unexpected error occurred getting clipboard text: {e}"
            )
            traceback.print_exc()
            return None

    def run_analysis_workflow(self):
        """
        The core workflow triggered by the hotkey. Runs in a separate thread.
        Gets text from clipboard, analyzes it, and speaks the result.
        """
        try:
            self.listener.set_query_running(True)

            # add little delay to avoid not getting the clipboard text
            time.sleep(0.1)

            # 1. Get Text from Clipboard
            print("Getting text from clipboard...")
            clipboard_text = self._get_clipboard_text()

            if not clipboard_text:
                print("Workflow aborted: Failed to get valid text from clipboard.")
                # Optionally provide audio feedback for failure
                # if self.speaker: self.speaker.speak("Clipboard empty or inaccessible.")
                return  # Exit workflow

            if self.listener.is_exit_requested():
                print("Workflow aborted: Exit requested.")
                return

            # 2. Analyze with Gemini using the new text method
            print("Requesting Gemini analysis for the text...")
            # Use the analyze_text method and the text prompt defined in config
            analysis_result = self.analyzer.analyze_text(clipboard_text)

            print("\n--- Gemini's Analysis ---")
            print(analysis_result)
            print("-------------------------")

            if self.listener.is_exit_requested():
                print("Workflow aborted: Exit requested.")
                return

            # 3. Speak with ElevenLabs
            if (
                self.speaker
                and not analysis_result.startswith(config.ERROR_PREFIX)
                and not analysis_result.startswith(config.BLOCKED_PREFIX)
            ):
                print("Attempting TTS...")
                success = self.speaker.speak(analysis_result)
                if not success:
                    print("TTS process indicated failure.")
                if self.listener.is_exit_requested():
                    print("Workflow aborted: Exit requested.")
                    return
            elif not self.speaker:
                print("Skipping TTS: Speaker not available.")
            else:
                # Speak the error/block message itself? Or just log?
                print(f"Skipping TTS: Analysis result was: {analysis_result}")
                # Example: Speak the error if desired
                # if self.speaker:
                #     self.speaker.speak(analysis_result)

        except Exception as e:
            print(
                f"{config.ERROR_PREFIX} An unexpected error occurred during the workflow: {e}"
            )
            traceback.print_exc()
            # Optionally speak a generic error message
            # if self.speaker: self.speaker.speak("An error occurred during analysis.")

        finally:
            # Cleanup (No temporary file to clean for text)
            self.listener.set_query_running(False)

            # Final message
            if not self.listener.is_exit_requested():
                print(
                    f"\nWorkflow complete. Listening for '{config.TRIGGER_HOTKEY_TEXT}'..."
                )
            # No explicit message needed if exiting

    # --- Application Lifecycle Methods (identical to main_screenshot.py) ---

    def start_listening(self):
        """Starts the injected hotkey listener."""
        if not self.listener.start():
            print("Exiting due to listener start failure.")
            sys.exit(1)

    def stop_listening(self):
        """Stops the injected hotkey listener."""
        self.listener.stop()

    def request_exit(self):
        """Signals the application to exit gracefully via the injected listener."""
        self.listener.request_exit()

    def run(self):
        """Runs the main application loop, starting the listener and waiting for exit."""
        print("--- Clipboard Text to Gemini Analysis ---")  # Updated title

        if not config.validate_config():
            print("Configuration validation failed. Exiting.")
            sys.exit(1)

        # Dependencies are injected via __init__
        self.start_listening()

        print(f"\nInitialization complete. Ready.")
        print(
            f"Trigger: '{config.TRIGGER_HOTKEY_TEXT}' | Exit: '{config.EXIT_HOTKEY_STR}'"
        )
        print("Press the trigger hotkey after copying text to the clipboard.")

        # --- Main Application Loop ---
        try:
            while not self.listener.is_exit_requested():
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt caught. Requesting shutdown.")
            self.request_exit()
        except Exception as main_loop_err:
            print(f"\n{config.ERROR_PREFIX} Error in main loop: {main_loop_err}")
            traceback.print_exc()
            self.request_exit()  # Attempt graceful exit
        finally:
            # --- Shutdown Sequence ---
            print("\nShutting down...")
            self.stop_listening()


# --- Signal Handling (identical to main_screenshot.py) ---
_app_instance: TextAnalyzerApp | None = None


def signal_handler(sig, frame):
    """Handles OS signals like Ctrl+C (SIGINT) or termination (SIGTERM)."""
    try:
        signal_name = signal.Signals(sig).name
    except ValueError:
        signal_name = f"Signal {sig}"
    print(f"\n{signal_name} received, initiating shutdown...")
    if _app_instance:
        _app_instance.request_exit()
    else:
        print("Error: App instance not found for signal handler.")  # Keep this error


# --- Main Execution Block ---

if __name__ == "__main__":
    app: TextAnalyzerApp | None = None

    try:
        # --- Create Dependencies ---
        speaker = ElevenLabsSpeaker()
        analyzer = GeminiAnalyzer()
        listener_instance = HotkeyListener(
            trigger_hotkey_str=config.TRIGGER_HOTKEY_TEXT,
            exit_hotkey_str=config.EXIT_HOTKEY_STR,
        )

        # --- Create Main Application ---
        app = TextAnalyzerApp(
            speaker=speaker,
            analyzer=analyzer,
            listener=listener_instance,
        )

        # --- Link Listener Callback ---
        listener_instance._add_callback(app.run_analysis_workflow)

        _app_instance = app  # Assign for signal handler

        # --- Setup Signal Handlers ---
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            print(
                "Warning: Could not set signal handlers (running in non-main thread?)"
            )
        except Exception as e:
            print(f"Warning: Could not set signal handlers: {e}")

        # --- Run the Application ---
        app.run()

    except (RuntimeError, ValueError, TypeError) as init_error:
        print(f"\n{config.ERROR_PREFIX} Initialization Failed: {init_error}")
        traceback.print_exc()  # Show details for init errors
        sys.exit(1)
    except Exception as critical_error:
        print(f"\n{config.ERROR_PREFIX} CRITICAL UNEXPECTED ERROR: {critical_error}")
        traceback.print_exc()
        if listener_instance:
            print("Attempting emergency listener stop...")
            listener_instance.stop()
        sys.exit(1)
    finally:
        print("Exiting script.")
