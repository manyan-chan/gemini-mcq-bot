# tts_speaker.py
import sys

from elevenlabs import stream as elevenlabs_stream
from elevenlabs.client import ElevenLabs

import config  # Keep config separate for clarity


class ElevenLabsSpeaker:
    """
    Handles Text-to-Speech generation and usage reporting using the ElevenLabs API.

    Manages the API client instance and provides methods for speaking text
    and retrieving usage information.
    """

    def __init__(self):
        """Initializes the ElevenLabsSpeaker, but defers client creation."""
        self._client = None
        self._api_key = config.ELEVENLABS_API_KEY
        self._voice_id = config.ELEVENLABS_VOICE_ID
        self._model_id = config.ELEVENLABS_MODEL
        self._error_prefix = getattr(
            config, "ERROR_PREFIX", "Error:"
        )  # Use config prefix or default

        if not self._api_key:
            print(
                "Warning: ELEVENLABS_API_KEY not found in config. Client will not be initialized."
            )

    def _get_client(self) -> ElevenLabs | None:
        """
        Lazily initializes and returns the ElevenLabs client instance.
        Handles initialization errors and API key checks.

        Returns:
            ElevenLabs client instance or None if initialization fails.
        """
        if self._client is None:
            if not self._api_key:
                # Warning already printed in __init__
                return None

            print("Initializing ElevenLabs client...")
            try:
                self._client = ElevenLabs(api_key=self._api_key)
                print("ElevenLabs client initialized successfully.")
            except Exception as e:
                print(f"{self._error_prefix} Error initializing ElevenLabs client: {e}")
                self._client = None  # Ensure client remains None on failure
                return None
        return self._client

    def _reset_client(self) -> None:
        """Resets the client instance, forcing re-initialization on next use."""
        print("Resetting ElevenLabs client instance.")
        self._client = None

    def speak(self, text_to_speak: str) -> bool:
        """
        Uses the ElevenLabs API to generate and stream audio for the given text.

        Args:
            text_to_speak: The text string to be converted to speech.

        Returns:
            True if speech was successfully generated and streamed, False otherwise.
        """
        if not text_to_speak:
            print("TTS: No text provided.")
            return False

        client = self._get_client()
        if not client:
            print(
                f"{self._error_prefix} Cannot speak: ElevenLabs client not available."
            )
            return False

        print("\nAttempting TTS with ElevenLabs...")
        try:
            print(
                f"Generating audio stream (Voice: {self._voice_id}, Model: {self._model_id})..."
            )
            audio_stream = client.text_to_speech.convert_as_stream(
                text=text_to_speak,
                voice_id=self._voice_id,
                model_id=self._model_id,
            )

            print("Streaming audio...")
            elevenlabs_stream(audio_stream)
            print("TTS: Finished speaking.")
            return True

        except Exception as e:
            print(f"{self._error_prefix} An error occurred during ElevenLabs TTS: {e}")
            if "authentication" in str(e).lower() or "401" in str(e):
                print("Hint: Check your ELEVENLABS_API_KEY.")
                self._reset_client()  # Reset client on auth error
            elif "quota" in str(e).lower():
                print("Hint: Check your ElevenLabs character quota.")
            return False

    def print_usage_info(self):
        """Fetches and prints the current ElevenLabs character usage information."""
        print("\nAttempting to fetch subscription info...")
        client = self._get_client()  # Use the instance's client getter

        if not client:
            print(
                f"{self._error_prefix} Could not fetch subscription info: Client not available."
            )
            return

        try:
            subscription_info = client.user.get_subscription()
            used = subscription_info.character_count
            limit = subscription_info.character_limit
            remaining = limit - used

            # Format numbers with commas for readability
            print("\n--- ElevenLabs Usage Info ---")
            print(f"Character Usage:  {used:,} / {limit:,}")
            print(f"Characters Left:  {remaining:,}")
            print(f"Subscription Tier: {subscription_info.tier}")
            print(f"Status:           {subscription_info.status}")
            print("-----------------------------")

        except Exception as e:
            print(f"\n{self._error_prefix} Could not fetch subscription info: {e}")
            # Reset client if fetching fails due to auth error
            if "authentication" in str(e).lower() or "401" in str(e):
                print("Hint: Check your ELEVENLABS_API_KEY.")
                self._reset_client()


# --- Test Execution Block ---
if __name__ == "__main__":
    print("--- Running tts_speaker.py in Test Mode ---")

    # 1. Check if the API key is configured (essential for testing)
    #    The class __init__ now handles the warning.
    if not config.ELEVENLABS_API_KEY:
        print(
            f"{getattr(config, 'ERROR_PREFIX', 'Error:')} ELEVENLABS_API_KEY is not set in config.py or .env file."
        )
        print("Cannot perform TTS test.")
        sys.exit(1)
    else:
        print("ElevenLabs API Key found in config.")

    # 2. Create an instance of the speaker
    speaker = ElevenLabsSpeaker()

    # 3. Define sample text
    sample_text = "Hello world."
    print(f"\nAttempting to speak: '{sample_text}'")

    # 4. Call the speak method on the instance
    success = speaker.speak(sample_text)

    if success:
        print("\nTTS Test Completed Successfully.")
    else:
        print("\nTTS Test Failed.")

    # 5. Fetch and print usage info using the instance method
    speaker.print_usage_info()

    print("\n--- Exiting Test Mode ---")
