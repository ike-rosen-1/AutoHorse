import streamlit as st
import requests
import json
import io

# --- Configuration ---
# Set the page title, icon, and layout. This is the first command Streamlit runs.
st.set_page_config(
    page_title="Horse Racing AI Assistant",
    page_icon="🐎",
    layout="wide"
)

# --- App Header ---
st.title("🐎 Horse Racing AI Assistant")
st.write("Welcome! This tool automates the AI-driven analysis of Brisnet DRF files.")

# --- Core Logic ---
# Retrieve the secure webhook URL from Streamlit's secrets management.
# This is the safest way to store sensitive information like URLs or API keys.
MAKE_WEBHOOK_URL = st.secrets.get("MAKE_WEBHOOK_URL")

# Function to call the Make.com workflow.
def run_analysis(uploaded_file):
    """Sends the uploaded file to the Make.com webhook and returns the JSON response."""
    if not MAKE_WEBHOOK_URL:
        st.error("Webhook URL is not configured. Please set it in your Streamlit secrets.")
        return None

    # We send the file using 'multipart/form-data', which is what Make.com expects.
    # The key 'file' must match the key you used when testing in Postman.
    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    
    try:
        response = requests.post(MAKE_WEBHOOK_URL, files=files)
        # Raise an exception if the request returned an error status code.
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while contacting the analysis workflow: {e}")
        st.error(f"Response Body: {response.text}") # Show the raw error from Make/Pipedream
        return None

# --- Main App Interface ---

# Initialize the chat history in Streamlit's session state.
# This ensures the chat history persists even when the user interacts with the app.
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Please upload your DRF file to begin."}]

# Display the existing chat messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # The content can be a string, or a dictionary/list for st.json
        if isinstance(message["content"], dict) or isinstance(message["content"], list):
            st.json(message["content"])
        else:
            st.write(message["content"])

# Create the file uploader widget. The app will wait here until a file is uploaded.
uploaded_file = st.file_uploader(
    "Choose a DRF file to analyze", 
    type=['txt', 'csv', 'drf'] # You can specify the allowed file types
)

# This block of code runs ONLY after a file has been successfully uploaded.
if uploaded_file is not None:
    # To prevent re-running on every single interaction, we check if we've already processed this file.
    if st.session_state.get("last_processed_file") != uploaded_file.name:
        
        # Display a "thinking" message to the user.
        with st.chat_message("assistant"):
            with st.spinner(f"Processing {uploaded_file.name}... This may take a moment."):
                # Call our main analysis function.
                results = run_analysis(uploaded_file)
        
        # If the analysis was successful, display the results.
        if results:
            # First, get the summary from the Python script's output
            python_summary = results.get('data', {}).get('python_summary', 'No summary available.')
            
            # Create a user-friendly summary message.
            summary_message = f"✅ Analysis Complete! {python_summary}."
            st.session_state.messages.append({"role": "assistant", "content": summary_message})
            
            # This is a placeholder for where your AI's plan will go.
            # For now, we'll just show the raw 'lean' data in a collapsed expander.
            with st.chat_message("assistant"):
                st.write("Here is the processed 'Lean' data ready for AI analysis:")
                with st.expander("View Processed Lean Data"):
                    st.json(results.get('data', {}).get('lean', 'No lean data found.'))

            # Store the name of the processed file to avoid re-running.
            st.session_state.last_processed_file = uploaded_file.name
            
            # Rerun the script to display the new messages we just added.
            st.rerun()

# This is a placeholder for future functionality (Phase 3).
if prompt := st.chat_input("Ask a follow-up question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # In the future, you would add logic here to send this prompt back to your Make.com workflow.
    st.session_state.messages.append({"role": "assistant", "content": "Follow-up questions are not yet implemented."})
    st.rerun()