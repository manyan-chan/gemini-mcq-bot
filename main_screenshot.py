# main.py
import signal
import sys
import time
import traceback  # Import traceback for detailed error logging

# Import our modules
import config
import utils
from gemini_analyzer import GeminiAnalyzer  # Import the class
from hotkey_listener import HotkeyListener  # Import the class
from tts_speaker import ElevenLabsSpeaker  # Import the class


class ScreenshotAnalyzerApp:
    """
    Orchestrates the screenshot analysis application using injected dependencies.
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
        # Assign injected dependencies
        self.speaker = speaker
        self.analyzer = analyzer
        self.listener = listener
        # Initialization messages handled by the creators or kept minimal

    def run_analysis_workflow(self):
        """
        The core workflow triggered by the hotkey. Runs in a separate thread.
        """
        screenshot_path = None
        try:
            self.listener.set_query_running(True)

            # 1. Take Screenshot
            print("Taking screenshot...")
            screenshot_path = utils.take_screenshot()
            if not screenshot_path:
                print("Workflow aborted: Failed to take screenshot.")
                return  # Exit if screenshot failed

            if self.listener.is_exit_requested():
                print("Workflow aborted: Exit requested.")
                return

            # 2. Analyze with Gemini
            print("Requesting Gemini analysis...")
            analysis_result = self.analyzer.analyze_image(screenshot_path)

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
                print("Skipping TTS: Analysis result indicated an error or block.")

        except Exception as e:
            print(
                f"{config.ERROR_PREFIX} An unexpected error occurred during the workflow: {e}"
            )
            traceback.print_exc()
        finally:
            # Cleanup and Reset State
            utils.cleanup_file(screenshot_path)
            self.listener.set_query_running(False)

            # Final message
            if not self.listener.is_exit_requested():
                print(
                    f"\nWorkflow complete. Listening for '{config.TRIGGER_HOTKEY_SCREENSHOT}'..."
                )
            # No explicit message needed if exiting

    # --- Application Lifecycle Methods ---

    def start_listening(self):
        """Starts the injected hotkey listener."""
        # Listener prints its own start message if successful
        if not self.listener.start():
            print("Exiting due to listener start failure.")
            sys.exit(1)

    def stop_listening(self):
        """Stops the injected hotkey listener."""
        self.listener.stop()  # Listener prints its own stop message

    def request_exit(self):
        """Signals the application to exit gracefully via the injected listener."""
        # Listener prints exit request message
        self.listener.request_exit()

    def run(self):
        """Runs the main application loop, starting the listener and waiting for exit."""
        print("--- Screenshot to Gemini Analysis ---")

        if not config.validate_config():
            print("Configuration validation failed. Exiting.")
            sys.exit(1)

        # Dependencies are injected via __init__
        self.start_listening()

        print(f"\nInitialization complete. Ready.")
        print(
            f"Trigger: '{config.TRIGGER_HOTKEY_SCREENSHOT}' | Exit: '{config.EXIT_HOTKEY_STR}'"
        )

        # --- Main Application Loop ---
        try:
            # Wait for exit request
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


# --- Signal Handling ---
_app_instance: ScreenshotAnalyzerApp | None = None


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


# --- Main Execution Block (Simplified) ---

if __name__ == "__main__":
    app: ScreenshotAnalyzerApp | None = None
    listener_instance: HotkeyListener | None = None  # Define here for finally block

    try:
        # --- Create Dependencies ---
        speaker: ElevenLabsSpeaker | None = None
        if config.ELEVENLABS_API_KEY:
            try:
                speaker = ElevenLabsSpeaker()
            except Exception as e:
                print(f"{config.ERROR_PREFIX} Failed to create Speaker: {e}")
        analyzer = GeminiAnalyzer()
        listener_instance = HotkeyListener(
            trigger_hotkey_str=config.TRIGGER_HOTKEY_SCREENSHOT,
            exit_hotkey_str=config.EXIT_HOTKEY_STR,
        )

        # --- Create Main Application ---
        app = ScreenshotAnalyzerApp(
            speaker=speaker,
            analyzer=analyzer,
            listener=listener_instance,
        )

        # --- Link Listener Callback ---
        # Assumes HotkeyListener has set_workflow_callback or similar method added
        listener_instance._add_callback(app.run_analysis_workflow)

        _app_instance = app  # Assign for signal handler

        # --- Setup Signal Handlers ---
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            print(f"Warning: Could not set signal handlers: {e}")

        # --- Run the Application ---
        app.run()

    except (RuntimeError, ValueError, TypeError) as init_error:
        print(f"\n{config.ERROR_PREFIX} Initialization Failed: {init_error}")
        # traceback.print_exc() # Can uncomment for debug
        sys.exit(1)
    except Exception as critical_error:
        print(f"\n{config.ERROR_PREFIX} CRITICAL UNEXPECTED ERROR: {critical_error}")
        traceback.print_exc()
        # Attempt emergency cleanup
        if listener_instance:  # Use the instance created in the try block
            print("Attempting emergency listener stop...")
            listener_instance.stop()
        sys.exit(1)
    finally:
        print("Exiting script.")
        # No explicit sys.exit(0) needed here, script ends naturally
