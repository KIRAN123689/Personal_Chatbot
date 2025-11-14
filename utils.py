# utils.py
# This file contains all the helper functions for API calls and response parsing,
# making the main app.py file cleaner and more focused on the UI logic.

import requests
import json
import time
import base64
from typing import Dict, List, Any
import streamlit as st

# --- API Configuration ---
# IMPORTANT: Replace with your actual Groq API key.
# Groq API for text chat and analysis
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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" # Replace with your Groq API key

# Pollination AI for image generation
# This is a public, free endpoint that does not require an API key.
POLLINATION_API_URL = "https://image.pollinations.ai/prompt/"

def call_groq_api(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calls the Groq API with exponential backoff for retries.
    """
    payload = {
        "model": "llama3-8b-8192",
        "messages": chat_history,
        "stream": False
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            response = requests.post(GROQ_API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                delay = (2 ** retry_count) + (time.time() - int(time.time()))
                st.warning(f"Rate limit exceeded. Retrying in {delay:.2f}s...")
                time.sleep(delay)
                retry_count += 1
            else:
                st.error(f"HTTP Error: {e}")
                return None
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None
    st.error("Maximum retries reached. Please try again later.")
    return None

def call_pollination_ai_api(prompt: str) -> str:
    """
    Calls the Pollination AI public API to generate an image from a prompt.
    Returns the base64 encoded image data.
    """
    # The prompt needs to be URL-encoded to handle spaces and special characters.
    url_encoded_prompt = requests.utils.quote(prompt)
    image_url = f"{POLLINATION_API_URL}{url_encoded_prompt}"
    
    with st.spinner("Generating image with Pollination AI..."):
        try:
            # We make a GET request to the image URL, which returns the image bytes directly.
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Encode the image content to base64 for display in Streamlit.
            return base64.b64encode(image_response.content).decode("utf-8")
            
        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error from Pollination AI: {e}")
            return None
        except Exception as e:
            st.error(f"An error occurred with image generation: {e}")
            return None

def get_groq_response_text(response_json: Dict[str, Any]) -> str:
    """
    Parses the Groq JSON response and returns the message content.
    """
    try:
        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"]
        else:
            return "I'm sorry, I couldn't generate a response."
    except (json.JSONDecodeError, KeyError):
        return "An error occurred while processing the API response."
