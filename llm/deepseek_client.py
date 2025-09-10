"""
DeepSeek LLM client for JSON-only completions
"""

import json
import requests
import os
from typing import Dict, Any, Optional


class DeepSeekClient:
    """Client for DeepSeek API with JSON-only response format"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key not provided. Set DEEPSEEK_API_KEY environment variable."
            )

        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(self, messages: list, model: str = "deepseek-chat") -> Dict[str, Any]:
        """
        Make a completion request with JSON response format

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name to use

        Returns:
            Parsed JSON response
        """
        payload = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 4000,
        }

        try:
            response = requests.post(
                self.base_url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse the JSON content
            return json.loads(content)

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {e}")

    def complete_with_system_prompt(
        self, user_message: str, system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Complete with system prompt

        Args:
            user_message: User message content
            system_prompt: System prompt (uses default if None)

        Returns:
            Parsed JSON response
        """
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        return self.complete(messages)

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt"""
        return """You are a precise tool-builder. You must return **valid JSON** that exactly matches the requested schema. Do not include any prose outside JSON. You **do not** have access to images; reason only from structured inputs. Prefer simple, robust Python (pandas + matplotlib). Figures must save under `./artifacts/` and never call `plt.show()`."""
