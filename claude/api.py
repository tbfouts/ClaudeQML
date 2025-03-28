"""
Claude API interactions module
"""
import os
import requests


def is_valid_api_key(api_key):
    """
    Validate an Anthropic API key by making a minimal API call
    Returns True if valid, False otherwise
    """
    if not api_key or len(api_key) < 20:  # Basic length check
        return False
        
    # Try to make a simple API call to validate
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Request with minimal tokens to check auth only
        data = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello"}]}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=5  # Short timeout just for validation
        )
        
        # Check if the response is valid (even if rate limited)
        return response.status_code == 200 or response.status_code == 429
        
    except Exception:
        return False


def ask_claude(prompt, message_history=None):
    """Ask Claude API a question and return the response"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return None
    
    try:
        # API endpoint and headers
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Initialize message history if not provided
        if message_history is None:
            message_history = []
            
        # Add current prompt to message history
        message_history.append({"role": "user", "content": prompt})
        
        # Request payload
        data = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 4000,
            "temperature": 0.7,
            "messages": message_history
        }
        
        # Make the API call to Anthropic directly
        response = requests.post(url, headers=headers, json=data)
        
        # Check for errors
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        # Parse the response
        response_data = response.json()
        result = response_data['content'][0]['text'].strip()
        
        # Add response to message history
        message_history.append({"role": "assistant", "content": result})
        
        # Return both result and updated message history
        return result, message_history
        
    except Exception as e:
        print(f"Error asking Claude: {str(e)}")
        return None, message_history