# gemini_analyzer.py

import google.generativeai as genai
from PIL import Image

import config  # Import our config constants


class GeminiAnalyzer:
    """
    Handles image analysis using the Google Gemini API.

    Encapsulates API configuration, model interaction, and response handling.
    """

    def __init__(self):
        """
        Initializes the GeminiAnalyzer and configures the API.
        """
        print("Initializing Gemini Analyzer...")
        self.api_key = config.GOOGLE_API_KEY
        self.model_name = config.GEMINI_MODEL_NAME
        self.prompt = config.GEMINI_INSTRUCTION_PROMPT
        self.error_prefix = config.ERROR_PREFIX
        self.blocked_prefix = config.BLOCKED_PREFIX
        genai.configure(api_key=self.api_key)  # type: ignore

    def analyze_image(self, image_path: str) -> str:
        """
        Sends the image at the given path to the configured Gemini model for analysis.

        Args:
            image_path: The file path to the image to be analyzed.

        Returns:
            A string containing the analysis result, or an error/blocked message
            prefixed according to the config.
        """
        try:
            # Initialize model instance for this request
            # Creating it here allows potentially changing model settings later if needed
            model = genai.GenerativeModel(self.model_name)  # type: ignore

            print("Loading image for Gemini...")
            with Image.open(image_path) as img:
                # Ensure image format is suitable (e.g., convert RGBA to RGB if needed)
                if img.mode == "RGBA":
                    print("Converting RGBA image to RGB for Gemini...")
                    img = img.convert("RGB")

                print(f"Sending image to Gemini model '{self.model_name}'...")

                # Generate content using the configured prompt and loaded image
                response = model.generate_content([self.prompt, img])

                # Parse the response using a helper method
                return self._parse_response(response)

        except Exception as e:
            return str(e)

    def analyze_text(self, text_content: str) -> str:
        """
        Sends the provided text content to the configured Gemini model for analysis.
        Uses the text-specific prompt.

        Args:
            text_content: The text string to be analyzed.

        Returns:
            A string containing the analysis result, or an error/blocked message
            prefixed according to the config.
        """
        if not self.api_key:
            return (
                f"{self.error_prefix} Cannot analyze text: GOOGLE_API_KEY is missing."
            )
        if not text_content or not text_content.strip():
            return f"{self.error_prefix} No text content provided for analysis."

        try:
            model = genai.GenerativeModel(self.model_name)  # type: ignore
            print(f"Sending text to Gemini model '{self.model_name}'...")

            # Use the text prompt and the text content
            response = model.generate_content([self.prompt, text_content])

            return self._parse_response(response)

        except Exception as e:
            print(f"Error during Gemini text analysis: {e}")
            # Potentially log traceback here for debugging
            return f"{self.error_prefix} Failed to analyze text: {e}"

    def _parse_response(self, response) -> str:
        """Parses the response object from Gemini."""
        try:
            # --- Enhanced Response Handling ---
            if not response.candidates:
                # Check for blocking feedback even if candidates list is empty
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    reason = (
                        response.prompt_feedback.block_reason.name
                    )  # Use name for readability
                    return f"{self.blocked_prefix} due to safety concerns ({reason})."
                else:
                    # Log the full response for debugging if possible
                    # print(f"Debug: Gemini Response Details: {response}")
                    return f"{self.error_prefix} Gemini returned no candidates in response."

            candidate = response.candidates[0]  # Get the first candidate

            # Success case: Extract text
            analysis_text = candidate.content.parts[0].text
            print("Gemini analysis received.")
            return analysis_text.strip()
            # --- End Enhanced Response Handling ---

        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            # print(f"Debug: Full Gemini Response on Parse Error: {response}") # Optional debug
            return f"{self.error_prefix} Failed to parse Gemini response: {e}"


if __name__ == "__main__":
    print("--- Running gemini_analyzer.py in Test Mode ---")

    # Create a dummy image file for testing if it doesn't exist
    TEST_IMAGE_PATH = "test_screenshot.png"

    # 1. Create an instance of the analyzer
    analyzer = GeminiAnalyzer()

    # 2 Call the analyze_image method
    print(f"\nAttempting to analyze image: '{TEST_IMAGE_PATH}'")
    result = analyzer.analyze_image(TEST_IMAGE_PATH)

    # 3. Print the result
    print("\n--- Analysis Result ---")
    print(result)
    print("-----------------------")
    print("\n--- Exiting Test Mode ---")
