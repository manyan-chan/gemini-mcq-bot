# hotkey_listener.py
import sys
import threading
from typing import Callable, Optional, Set

from pynput import keyboard


class HotkeyListener:
    """
    Manages keyboard event listening for trigger and exit hotkeys.

    Encapsulates listener state, including currently pressed keys,
    running query status, and exit flags. Spawns the workflow
    callback in a separate thread upon trigger detection.
    """

    # Static key map for parsing - doesn't need to be per-instance
    _KEY_MAP = {
        "shift": keyboard.Key.shift,
        "ctrl": keyboard.Key.ctrl,
        "alt": keyboard.Key.alt,
        "cmd": keyboard.Key.cmd,
        "win": keyboard.Key.cmd,
        "command": keyboard.Key.cmd,
        "esc": keyboard.Key.esc,
        "space": keyboard.Key.space,
        "enter": keyboard.Key.enter,
        "tab": keyboard.Key.tab,
        "backspace": keyboard.Key.backspace,
        "delete": keyboard.Key.delete,
        "up": keyboard.Key.up,
        "down": keyboard.Key.down,
        "left": keyboard.Key.left,
        "right": keyboard.Key.right,
        "page_up": keyboard.Key.page_up,
        "page_down": keyboard.Key.page_down,
        "home": keyboard.Key.home,
        "end": keyboard.Key.end,
        "f1": keyboard.Key.f1,
        "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5,
        "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7,
        "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11,
        "f12": keyboard.Key.f12,
    }

    def __init__(
        self,
        trigger_hotkey_str: str,
        exit_hotkey_str: str,
    ):
        """
        Initializes the HotkeyListener.

        Args:
            trigger_hotkey_str: String representation of the trigger hotkey (e.g., "shift+space").
            exit_hotkey_str: String representation of the exit hotkey (e.g., "esc").
            workflow_callback: The function to call when the trigger hotkey is detected.

        Raises:
            ValueError: If hotkey strings are invalid or exit key is not a single key.
        """
        print("Initializing HotkeyListener...")
        self._current_keys: Set[keyboard.Key | keyboard.KeyCode] = set()
        self._exit_app_flag = threading.Event()
        self._is_running_query = False
        self._lock = threading.Lock()  # Lock protects _is_running_query
        self._listener: Optional[keyboard.Listener] = None

        print("Parsing hotkeys...")
        self._trigger_combination = self._parse_hotkey_string(trigger_hotkey_str)
        parsed_exit = self._parse_hotkey_string(exit_hotkey_str)

        if not self._trigger_combination:
            raise ValueError(
                f"Error parsing trigger hotkey string: '{trigger_hotkey_str}'"
            )
        if not parsed_exit:
            raise ValueError(f"Error parsing exit hotkey string: '{exit_hotkey_str}'")
        if len(parsed_exit) != 1:
            raise ValueError(f"Exit hotkey must be a single key: '{exit_hotkey_str}'")

        self._exit_key_obj = list(parsed_exit)[0]

        print(f" Trigger Hotkey: {' + '.join(map(str, self._trigger_combination))}")
        print(f" Exit Hotkey: {str(self._exit_key_obj)}")

    def _add_callback(self, callback: Callable[[], None]):
        """
        Adds a callback to be executed when the trigger hotkey is detected.

        Args:
            callback: The function to call when the trigger hotkey is detected.
        """
        self._workflow_callback = callback

    def start(self) -> bool:
        """Starts the keyboard listener in a separate thread."""
        if self._listener and self._listener.is_alive():
            print("Listener already running.")
            return True  # Indicate it's already started

        print("Attempting to start keyboard listener...")
        try:
            # Create and start the listener thread
            self._listener = keyboard.Listener(
                on_press=self._on_press,  # type: ignore
                on_release=self._on_release,  # type: ignore
                suppress=False,  # Avoid suppressing keys globally unless needed
            )
            self._listener.start()
            print("Listener started successfully.")
            return True
        except Exception as e:
            print(f"Failed to start listener: {e}")
            # Add platform-specific hints
            if sys.platform == "darwin" and (
                "permission" in str(e).lower() or "secure input" in str(e).lower()
            ):
                print(
                    "Hint: macOS requires 'Accessibility'/'Input Monitoring' permissions for Python/Terminal."
                )
            elif sys.platform == "linux" and (
                "permission" in str(e).lower() or "root" in str(e).lower()
            ):
                print(
                    "Hint: Linux might require root privileges or user added to the 'input' group."
                )
            self._listener = None  # Ensure listener is None on failure
            return False

    def stop(self):
        """Stops the keyboard listener thread."""
        # Note: pynput listener stop is sometimes not immediate.
        if self._listener:  # Check if instance exists
            if self._listener.is_alive():
                print("Stopping listener...")
                try:
                    # pynput's stop() signals the listener thread to exit.
                    # It doesn't block indefinitely but might take a moment.
                    self._listener.stop()
                    # We don't necessarily need to join() here, main loop handles exit wait.
                    print("Listener stop requested.")
                except Exception as e:
                    print(f"Error stopping listener thread: {e}")
            else:
                # print("Listener was already stopped.") # Optional logging
                pass
            self._listener = None  # Clear the reference
        else:
            # print("Listener was not running or instance is None.") # Optional logging
            pass

    def request_exit(self):
        """Signals the application that an exit is requested."""
        if not self._exit_app_flag.is_set():
            print("Exit requested via listener method.")
            self._exit_app_flag.set()
            self.stop()  # Also stop the listener when exit is requested

    def wait_for_exit(self):
        """Blocks the calling thread until an exit is requested."""
        self._exit_app_flag.wait()

    def is_exit_requested(self) -> bool:
        """Checks if an application exit has been signaled."""
        return self._exit_app_flag.is_set()

    # --- State Management (used by main Application/Workflow) ---

    def set_query_running(self, status: bool):
        """
        Sets the status indicating whether the workflow callback is active.
        This should be called by the workflow itself.
        """
        with self._lock:
            # print(f"Listener state: Setting query running = {status}") # Debug logging
            self._is_running_query = status

    # --- Internal Methods ---

    def _is_query_running_internal(self) -> bool:
        """Internal check for query status, used by _on_press."""
        with self._lock:
            return self._is_running_query

    def _parse_hotkey_string(
        self, hotkey_str: str
    ) -> Optional[Set[keyboard.Key | keyboard.KeyCode]]:
        """Parses a hotkey string (e.g., 'ctrl+shift+a') into pynput key objects."""
        parts = hotkey_str.lower().split("+")
        keys = set()
        for part in parts:
            part = part.strip()
            if part in self._KEY_MAP:
                keys.add(self._KEY_MAP[part])
            elif len(part) == 1:
                try:
                    keys.add(keyboard.KeyCode.from_char(part))
                except ValueError:
                    print(
                        f"Warning: Invalid character '{part}' in hotkey string '{hotkey_str}'"
                    )
                    return None
            else:
                # Try finding special keys by name (e.g., 'page_down')
                try:
                    key_attr = getattr(keyboard.Key, part, None)
                    if key_attr:
                        keys.add(key_attr)
                    else:
                        print(
                            f"Warning: Unrecognized key part '{part}' in hotkey string '{hotkey_str}'"
                        )
                        return None
                except Exception:  # Catch potential errors during getattr or adding
                    print(
                        f"Warning: Error processing key part '{part}' in hotkey string '{hotkey_str}'"
                    )
                    return None
        return keys if keys else None

    def _normalize_key(self, key) -> keyboard.Key | keyboard.KeyCode:
        """Normalizes modifier keys (e.g., shift_l -> shift)."""
        if key in {keyboard.Key.shift_l, keyboard.Key.shift_r}:
            return keyboard.Key.shift
        if key in {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
            return keyboard.Key.ctrl
        if key in {keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}:
            return keyboard.Key.alt
        if key in {keyboard.Key.cmd_l, keyboard.Key.cmd_r}:  # macOS Command key
            return keyboard.Key.cmd
        # Add other normalizations if needed (e.g., numpad keys)
        return key

    # --- pynput Callbacks ---

    def _on_press(self, key) -> Optional[bool]:
        """Internal callback for key press events from pynput."""
        # Check if exit requested - if so, stop listener processing early
        if self.is_exit_requested():
            # Returning False from pynput listener callbacks stops the listener
            return False

        try:
            norm_key = self._normalize_key(key)
            self._current_keys.add(norm_key)

            # --- Check for Trigger Hotkey ---
            # Use issubset for combination check
            if self._trigger_combination is None:
                return None  # No trigger hotkey set, ignore
            if self._trigger_combination.issubset(self._current_keys):
                # Lock to check/prevent concurrent workflow starts
                with self._lock:
                    if not self._is_running_query:
                        # Important: DO NOT set _is_running_query=True here.
                        # The workflow itself should set it via set_query_running()
                        # once it actually starts processing.
                        if self._workflow_callback:
                            print("\n--- Trigger Hotkey Detected ---")
                            # Run the workflow in a separate thread so listener isn't blocked
                            thread = threading.Thread(
                                target=self._workflow_callback, daemon=True
                            )
                            thread.start()
                        else:
                            print(
                                "Warning: Trigger detected but no workflow callback is set."
                            )
                    # else: print("Trigger ignored, query already running.") # Debug

            # --- Check for Exit Key ---
            if norm_key == self._exit_key_obj:
                self.request_exit()  # Signal exit using the class method
                return False  # Stop the listener

        except Exception as e:
            print(f"Error in _on_press: {e}")
            # Decide if you want to stop the listener on error
            # self.request_exit()
            # return False
            return True  # Continue listener by default

        return None  # Indicate pynput should continue processing event

    def _on_release(self, key):
        """Internal callback for key release events from pynput."""
        # Check if exit requested - if so, stop listener processing early
        if self.is_exit_requested():
            return False  # Stop the listener

        try:
            norm_key = self._normalize_key(key)
            self._current_keys.discard(
                norm_key
            )  # Use discard to avoid errors if key not present
        except Exception as e:
            print(f"Error in _on_release: {e}")
            # Decide if you want to stop the listener on error
            # self.request_exit()
            # return False
            return True  # Continue listener by default

        return None  # Indicate pynput should continue processing event
