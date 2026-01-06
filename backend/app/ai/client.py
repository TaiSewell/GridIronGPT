"""
=============================================================
 File: client.py
 Author: Tai Sewell
 Description:
     Minimal OpenAI client wrapper for chat completions.
=============================================================
"""

from __future__ import annotations

from typing import List, Dict, Any

import httpx

from backend.app.config import settings


def run_chat_completion(
    messages: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> str:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"].strip()
