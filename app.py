# streamlit_app.py
# Requirements: google-genai
# Make sure to set your GEMINI_API_KEY in Streamlit secrets

import streamlit as st
import os
from google import genai
from google.genai import types

# Page configuration
st.set_page_config(page_title="Cold Email Hook Generator")

# Hardcoded user credentials
USER_CREDENTIALS = {
    "admin": "admin@9848",
    "mansi": "mansi@123"
}

def login():
    # Initialize login state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        # Stop execution until the user logs in
        st.stop()

def generate_hook(url: str, client: genai.Client, examples: str) -> str:
    """
    Calls the Gemini API with Google search tool to generate a 2-3 line cold email hook for the given URL.
    """
    prompt = f"""write starting hook of 2-3 lines for a cold emails for following site

{url}

make it personal and dont use any sales words, here are some examples

{examples}
"""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    tools = [types.Tool(google_search=types.GoogleSearch())]
    config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain"
    )

    # Stream the generated content
    result = ""
    for chunk in client.models.generate_content_stream(
        model="models/gemini-2.5-pro-exp-03-25",
        contents=contents,
        config=config
    ):
        result += chunk.text
    return result


def main():
    # User login
    login()

    st.title("Cold Email Hook Generator")
    st.write(f"Welcome, {st.session_state.username}!")
    st.markdown("Enter one or multiple URLs (one per line) to generate cold email hooks.")

    # Input area for URLs
    url_input = st.text_area(
        "URLs",
        placeholder="https://example.com\nhttps://example2.com"
    )

    # Example hooks to guide the model
    examples_text = """
I attended a jamming session hosted by Mike & Mike's Guitar Bar with a friend. I just loved how you're creating a welcoming environment for music enthusiasts, and I'm interested in learning guitar again.
They say behind every successful woman is a fabulous handbag, and I believe the same. Trusting Lotuff Leather for its best and timeless aesthetic, leather bags are the best decision ever.
For my mom’s 50th birthday, I wanted to surprise her with solitaire earrings. Without a second thought, I headed to London Jewelers and found the perfect pair, which looked stunning on her.
We all know that Health is wealth, and Lost Empire's herbal products are what I've been using regularly to boost my energy and balance my hormones, and I’m genuinely impressed with the results.
My pet found a way to escape from the house and gave us a hard time finding him, and that's when my friend suggested it to us, logistimatics, and I can't thank you enough for how helpful it is.
"""

    if st.button("Generate Hooks"):
        if not url_input.strip():
            st.error("Please enter at least one URL.")
        else:
            urls = [u.strip() for u in url_input.splitlines() if u.strip()]
            # Initialize Gemini client
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))#

            # Generate and display hooks for each URL
            for url in urls:
                st.subheader(f"Hook for {url}")
                with st.spinner("Generating..."):
                    try:
                        hook = generate_hook(url, client, examples_text)
                        st.text(hook)
                    except Exception as e:
                        st.error(f"Error generating hook: {e}")

if __name__ == "__main__":
    main()
