# Required libraries: streamlit, google-generativeai
# Save this code as app.py
# Create a requirements.txt file with:
# streamlit
# google-generativeai

import streamlit as st
import os
import google.generativeai as genai
from google.generativeai import types # Although not used in the final function, good practice to keep if planning tool use later
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# Attempt to get API key from Streamlit secrets, fallback to environment variable
# This allows the app to work both locally (with env var) and deployed (with secrets)
try:
    # Using st.secrets for deployment on Streamlit Community Cloud
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    logging.info("Loaded API key from Streamlit secrets.")
except (AttributeError, KeyError): # Handles case where st.secrets doesn't exist or key is missing
    # Fallback to environment variable for local development
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        logging.info("Loaded API key from environment variable.")
    else:
        logging.warning("GEMINI_API_KEY not found in Streamlit secrets or environment variables.")
        GEMINI_API_KEY = None # Ensure it's None if not found

# --- Static Credentials ---
# For a real application, use a database and proper authentication
VALID_USERNAME = "user"
VALID_PASSWORD = "password" # Simple password for this demo

# --- Gemini API Function ---
def generate_hook(url: str, api_key: str) -> str:
    """
    Calls the Gemini API to generate a personalized, non-salesy
    cold email hook (2-3 lines) for a given website URL.
    """
    if not api_key:
        logging.error("API Key is missing.")
        return "Error: GEMINI_API_KEY is not configured. Please set it in environment variables or Streamlit secrets."

    try:
        # Configure the Generative AI client
        genai.configure(api_key=api_key)

        # Define the specific prompt for generating the hook
        prompt = f"""
        write starting hook of 2-3 lines for a cold emails for the following site:
        {url}

        make it personal and dont use any sales words, here are some examples of the desired style:

        I attended a jamming session hosted by Mike & Mike's Guitar Bar with a friend. I just loved how you're creating a welcoming environment for music enthusiasts, and I'm interested in learning guitar again.
        They say behind every successful woman is a fabulous handbag, and I believe the same. Trusting Lotuff Leather for its best and timeless aesthetic, leather bags are the best decision ever.
        For my mom’s 50th birthday, I wanted to surprise her with solitaire earrings. Without a second thought, I headed to London Jewelers and found the perfect pair, which looked stunning on her.
        We all know that Health is wealth, and Lost Empire's herbal products are what I've been using regularly to boost my energy and balance my hormones, and I’m genuinely impressed with the results.
        My pet found a way to escape from the house and gave us a hard time finding him, and that's when my friend suggested it to us, logistimatics, and I can't thank you enough for how helpful it is.

        Focus ONLY on the website provided ({url}) and generate ONLY the 2-3 line hook text. Do NOT include any introductory phrases like "Here's a hook:" or similar introductions. Just provide the hook itself.
        """

        # Select the model - use a generally available model like gemini-1.5-flash
        # Check the Gemini documentation for the latest recommended model names.
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

        # Generate the content
        # No specific tools (like Google Search) seem necessary for this task,
        # as it relies on the model's knowledge or ability to infer from the URL/domain.
        response = model.generate_content(prompt)

        # Process the response
        if response.parts:
            # Extract the text from the first part
            generated_text = response.text.strip()
            logging.info(f"Successfully generated hook for {url}")
            return generated_text
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
             # Handle cases where the content generation was blocked
             block_reason = response.prompt_feedback.block_reason.name
             logging.warning(f"Content generation blocked for {url}. Reason: {block_reason}")
             return f"Error: Content generation blocked due to: {block_reason}. Please try a different URL or modify the prompt."
        else:
            # Handle unexpected empty responses
            logging.error(f"Received an empty response from the API for {url}.")
            return "Error: Received an empty response from the API. Please try again."

    except Exception as e:
        # Catch and log any other exceptions during the API call
        logging.error(f"Gemini API call failed for {url}: {e}", exc_info=True)
        # Provide specific feedback for common errors if possible
        if "API key not valid" in str(e):
             return "Error: The provided Gemini API Key is invalid or expired."
        elif "permission" in str(e).lower():
             return "Error: API key lacks permission for the requested model or service."
        # Generic error for other issues
        return f"Error: An unexpected error occurred while generating the hook. Details: {str(e)}"

# --- Streamlit App UI ---

# Initialize session state variable for login status if it doesn't exist
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- Login Screen Display Logic ---
# Show login form only if the user is not logged in
if not st.session_state.logged_in:
    st.title("Login")
    st.write("Use the demo credentials to access the generator.")

    with st.form("login_form"):
        username = st.text_input("Username", value="user") # Pre-fill for convenience
        password = st.text_input("Password", type="password", value="password") # Pre-fill
        submitted = st.form_submit_button("Login")

        if submitted:
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.logged_in = True
                logging.info("User logged in successfully.")
                # Use st.rerun() to immediately redraw the app in the logged-in state
                st.rerun()
            else:
                st.error("Invalid username or password")
                logging.warning("Failed login attempt.")

# --- Main Application Screen Logic ---
# Show the main app content only if the user is logged in
if st.session_state.logged_in:
    st.sidebar.success("Logged In") # Indicate login status in the sidebar

    # Logout Button in the sidebar
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        logging.info("User logged out.")
        # Rerun to show the login screen again
        st.rerun()

    # Main page content
    st.title("📧 Cold Email Hook Generator")
    st.markdown(
        "Enter a website URL below to generate a personalized, non-salesy "
        "opening hook (2-3 lines) for your cold emails, using Gemini AI."
    )
    st.markdown("---") # Visual separator

    # Input URL form
    with st.form("hook_generator_form"):
        input_url = st.text_input(
            "Website URL:",
            placeholder="e.g., https://meyersmanx.com/",
            help="Enter the full URL of the website you want to write about."
        )
        generate_button = st.form_submit_button("✨ Generate Hook")

        if generate_button:
            # Basic validation
            if not input_url:
                st.warning("Please enter a URL.")
            elif not (input_url.startswith("http://") or input_url.startswith("https://")):
                 st.warning("Please enter a valid URL starting with `http://` or `https://`")
            elif not GEMINI_API_KEY:
                 # Check API key again just before calling (important for deployment)
                 st.error("API Key is not configured. Cannot generate hook.")
                 logging.error("Generate button clicked but API key is missing.")
            else:
                # Show spinner during API call
                with st.spinner("🤖 Calling Gemini... Please wait..."):
                    logging.info(f"Requesting hook generation for URL: {input_url}")
                    hook_result = generate_hook(input_url, GEMINI_API_KEY)

                # Display results
                st.subheader("Generated Hook:")
                if hook_result.startswith("Error:"):
                    st.error(hook_result)
                    logging.error(f"Hook generation failed for {input_url}: {hook_result}")
                else:
                    # Use success box or text_area for easy copying
                    st.success(hook_result)
                    # st.text_area("Copy your hook:", hook_result, height=100) # Alternative display
                    logging.info(f"Successfully displayed hook for {input_url}")

    st.markdown("---")
    st.caption("Powered by Google Gemini | Developed with Streamlit")

# --- End of App ---
