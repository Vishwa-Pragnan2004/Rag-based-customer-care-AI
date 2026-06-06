import os
import logging
from typing import List, Dict
import requests

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-2.5-flash"
        if not self.api_key:
            logger.warning("[LLM] GEMINI_API_KEY environment variable is not set!")

    def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY is not configured. Please set the GEMINI_API_KEY environment variable."

        # Extract system prompt(s)
        system_prompts = [m["content"] for m in messages if m["role"] == "system"]
        system_instruction = "\n\n".join(system_prompts) if system_prompts else ""

        # Map other messages to Gemini's content format
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            
            # Map role
            role = m.get("role", "user")
            if role in ["bot", "assistant", "model"]:
                gemini_role = "model"
            else:
                gemini_role = "user"
                
            contents.append({
                "role": gemini_role,
                "parts": [{"text": m.get("content", "")}]
            })

        # Make sure contents is not empty
        if not contents:
            return ""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.2),
                "maxOutputTokens": kwargs.get("max_tokens", 512)
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            
            # Extract response text
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            
            return "Error: Could not extract text from Gemini response."
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            if 'response' in locals() and response is not None:
                logger.error(f"Response content: {response.text}")
            return f"Error calling Gemini API: {str(e)}"
