def load_templates():
    """Load templates from file if it exists, otherwise use defaults."""
    try:
        if pathlib.Path(TEMPLATES_FILE).exists():
            with open(TEMPLATES_FILE, "r") as f:
                templates = json.load(f)
                return templates.get("hook", DEFAULT_PROMPT_TEMPLATE), templates.get("fit", DEFAULT_FIT_TEMPLATE)
    except Exception as e:
        st.warning(f"Failed to load templates: {e}. Using defaults.")
    
    return DEFAULT_PROMPT_TEMPLATE, DEFAULT_FIT_TEMPLATE

def save_templates(hook_template, fit_template):
    """Save templates to file."""
    try:
        templates = {
            "hook": hook_template,
            "fit": fit_template
        }
        with open(TEMPLATES_FILE, "w") as f:
            json.dump(templates, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save templates: {e}")
        return False# Constants
TEMPLATES_FILE = "templates.json"# streamlit_app.py
# Requirements: google-genai, extra-streamlit-components
# Make sure to set your GEMINI_API_KEY in Streamlit secrets

import streamlit as st
import os
import json
from google import genai
from google.genai import types
import extra_streamlit_components as stx
import pathlib

# Page configuration
st.set_page_config(page_title="Cold Email Hook Generator")

# Hardcoded user credentials
USER_CREDENTIALS = {
    "admin": "admin@9848",
    "mansi": "mansi@123"
}

# Default prompt templates
DEFAULT_PROMPT_TEMPLATE = """write starting hook of 2-3 lines for a cold emails for following site

{url}

make it personal and dont use any sales words, here are some examples

{examples}
"""

DEFAULT_FIT_TEMPLATE = """Analyze the following website and determine which of our services would be the best fit for them:

Website: {url}

OUR SERVICES:
1. Digital Marketing Consultation
2. SEO & Content Strategy
3. Social Media Management
4. Email Marketing Campaigns
5. Website Design & Development
6. PPC & Google Ads Management
7. Marketing Automation
8. E-commerce Solutions

For each recommended service, provide a brief (1-2 sentence) explanation of why this would benefit them based on their website/business. Prioritize the top 3 services that would provide the most value.

Please format the response as:
RECOMMENDED SERVICES FOR {url}:
1. [Service Name]: [Brief explanation of fit & benefit]
2. [Service Name]: [Brief explanation of fit & benefit]
3. [Service Name]: [Brief explanation of fit & benefit]
"""

def get_cookie_manager():
    """Create and return a cookie manager instance."""
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    return st.session_state.cookie_manager

def login():
    # Get cookie manager
    cookie_manager = get_cookie_manager()
    
    # Initialize login state
    if "logged_in" not in st.session_state:
        # Check if login cookie exists
        cookies = cookie_manager.get_all()
        if "username" in cookies and "logged_in" in cookies:
            if cookies["logged_in"] == "true" and cookies["username"] in USER_CREDENTIALS:
                st.session_state.logged_in = True
                st.session_state.username = cookies["username"]
        else:
            st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me", value=True)
        
        if st.button("Login"):
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                
                # Set cookies if remember me is checked
                if remember_me:
                    cookie_manager.set("logged_in", "true", expires_at=None)  # No expiry for persistent login
                    cookie_manager.set("username", username, expires_at=None)
                
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        # Logout functionality
        if st.button("Logout"):
            cookie_manager.delete("logged_in")
            cookie_manager.delete("username")
            st.session_state.logged_in = False
            st.session_state.username = None
            st.success("Logged out successfully!")
            st.rerun()
            
        # Stop execution until the user logs in
        st.stop()
    
    # Add logout button when logged in
    if st.session_state.logged_in:
        # Place logout in sidebar
        with st.sidebar:
            if st.button("Logout"):
                cookie_manager = get_cookie_manager()
                cookie_manager.delete("logged_in")
                cookie_manager.delete("username")
                st.session_state.logged_in = False
                st.session_state.username = None
                st.success("Logged out successfully!")
                st.rerun()

def generate_content(prompt: str, client: genai.Client) -> str:
    """
    Calls the Gemini API with Google search tool to generate content based on the provided prompt.
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
        model="models/gemini-2.5-flash-preview-04-17",
        contents=contents,
        config=config
    ):
        result += chunk.text
    return result

def generate_hook(url: str, client: genai.Client, examples: str, prompt_template: str) -> str:
    """
    Generates a 2-3 line cold email hook for the given URL.
    """
    # Format the prompt using the template and inputs
    formatted_prompt = prompt_template.format(url=url, examples=examples)
    return generate_content(formatted_prompt, client)

def explore_fit(url: str, client: genai.Client, fit_template: str) -> str:
    """
    Analyzes a website and recommends which services would be a good fit.
    """
    # Format the prompt using the template and inputs
    formatted_prompt = fit_template.format(url=url)
    return generate_content(formatted_prompt, client)


def main():
    # Load saved templates or use defaults
    hook_template, fit_template = load_templates()
    
    # Initialize session state
    if "prompt_template" not in st.session_state:
        st.session_state.prompt_template = hook_template
    
    if "fit_template" not in st.session_state:
        st.session_state.fit_template = fit_template
        
    if "generated_hooks" not in st.session_state:
        st.session_state.generated_hooks = {}
    
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
For my mom's 50th birthday, I wanted to surprise her with solitaire earrings. Without a second thought, I headed to London Jewelers and found the perfect pair, which looked stunning on her.
We all know that Health is wealth, and Lost Empire's herbal products are what I've been using regularly to boost my energy and balance my hormones, and I'm genuinely impressed with the results.
My pet found a way to escape from the house and gave us a hard time finding him, and that's when my friend suggested it to us, logistimatics, and I can't thank you enough for how helpful it is.
"""

    # Advanced settings expander for prompt editing
    with st.expander("Advanced Settings"):
        tab1, tab2 = st.tabs(["Hook Template", "Fit Analysis Template"])
        
        with tab1:
            st.subheader("Customize Hook Prompt Template")
            st.info("You can edit the prompt template below. Use {url} for the website URL and {examples} for the example hooks.")
            
            edited_prompt = st.text_area(
                "Hook Prompt Template",
                value=st.session_state.prompt_template,
                height=250
            )
            
            # Save button to update the prompt template
            if st.button("Save Hook Template"):
                st.session_state.prompt_template = edited_prompt
                # Save to file for persistence
                if save_templates(edited_prompt, st.session_state.fit_template):
                    st.success("Hook prompt template updated and saved for future sessions!")
                else:
                    st.success("Hook prompt template updated for this session only!")
                
            # Reset button to restore default prompt
            if st.button("Reset Hook Template"):
                st.session_state.prompt_template = DEFAULT_PROMPT_TEMPLATE
                # Save to file for persistence
                if save_templates(DEFAULT_PROMPT_TEMPLATE, st.session_state.fit_template):
                    st.success("Hook prompt template reset to default and saved!")
                else:
                    st.success("Hook prompt template reset to default for this session only!")
                
        with tab2:
            st.subheader("Customize Fit Analysis Template")
            st.info("You can edit the fit analysis template below. Use {url} for the website URL.")
            
            edited_fit_prompt = st.text_area(
                "Fit Analysis Template",
                value=st.session_state.fit_template,
                height=250
            )
            
            # Save button to update the fit template
            if st.button("Save Fit Template"):
                st.session_state.fit_template = edited_fit_prompt
                # Save to file for persistence
                if save_templates(st.session_state.prompt_template, edited_fit_prompt):
                    st.success("Fit analysis template updated and saved for future sessions!")
                else:
                    st.success("Fit analysis template updated for this session only!")
                
            # Reset button to restore default fit prompt
            if st.button("Reset Fit Template"):
                st.session_state.fit_template = DEFAULT_FIT_TEMPLATE
                # Save to file for persistence
                if save_templates(st.session_state.prompt_template, DEFAULT_FIT_TEMPLATE):
                    st.success("Fit analysis template reset to default and saved!")
                else:
                    st.success("Fit analysis template reset to default for this session only!")

    if st.button("Generate Hooks"):
        if not url_input.strip():
            st.error("Please enter at least one URL.")
        else:
            urls = [u.strip() for u in url_input.splitlines() if u.strip()]
            # Initialize Gemini client
            client = genai.Client(api_key="AIzaSyAhn1tRxkzugpu1wKWASp2jRPGctOpXsWA")
            
            # Clear previous results
            st.session_state.generated_hooks = {}

            # Generate and display hooks for each URL
            for url in urls:
                st.subheader(f"Hook for {url}")
                with st.spinner("Generating..."):
                    try:
                        hook = generate_hook(url, client, examples_text, st.session_state.prompt_template)
                        st.session_state.generated_hooks[url] = hook
                        st.text(hook)
                        
                        # Add an "Explore Fit" button for each URL
                        if st.button(f"Explore Fit for {url}", key=f"fit_{url}"):
                            with st.spinner(f"Analyzing fit for {url}..."):
                                try:
                                    fit_analysis = explore_fit(url, client, st.session_state.fit_template)
                                    st.subheader(f"Service Recommendations for {url}")
                                    st.markdown(fit_analysis)
                                except Exception as e:
                                    st.error(f"Error analyzing fit: {e}")
                    except Exception as e:
                        st.error(f"Error generating hook: {e}")
    
    # Add a separate section for exploring fit for previously generated hooks
    if st.session_state.generated_hooks:
        st.divider()
        st.subheader("Explore Service Fit")
        st.info("Analyze which of your services would be the best fit for these websites.")
        
        # Create a selectbox for choosing which URL to analyze
        urls = list(st.session_state.generated_hooks.keys())
        selected_url = st.selectbox("Select a website to analyze", urls)
        
        if st.button("Analyze Service Fit"):
            # Initialize Gemini client
            client = genai.Client(api_key="AIzaSyAhn1tRxkzugpu1wKWASp2jRPGctOpXsWA")#eos.environ.get("GEMINI_API_KEY"))
            
            with st.spinner(f"Analyzing fit for {selected_url}..."):
                try:
                    fit_analysis = explore_fit(selected_url, client, st.session_state.fit_template)
                    st.subheader(f"Service Recommendations for {selected_url}")
                    st.markdown(fit_analysis)
                except Exception as e:
                    st.error(f"Error analyzing fit: {e}")

if __name__ == "__main__":
    main()