"""
LLM provider abstraction — supports LM Studio (OpenAI-compat) and Ollama.

Provider is selected via config["provider"]: "lmstudio" (default) or "ollama".

  chat(messages, config)     — for classify / judge (structured JSON responses)
  generate(prompt, config)   — for free-form text generation (test case generation)
"""

import requests

DEFAULT_TIMEOUT = 120


def _endpoint(config: dict) -> str:
    if config.get("provider", "lmstudio") == "ollama":
        return config.get("ollama_endpoint", "http://localhost:11434")
    return config.get("lmstudio_endpoint", "http://localhost:1234")


def chat(messages: list, config: dict, json_format: bool = True, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Send a chat request. Returns the assistant message content as a string."""
    provider = config.get("provider", "lmstudio")
    model    = config.get("model", "gemma-4-27b-it")
    temp     = config.get("temperature", 0.1)
    endpoint = _endpoint(config)

    if provider == "ollama":
        body = {
            "model":    model,
            "messages": messages,
            "options":  {"temperature": temp},
            "think":    config.get("think", False),
            "stream":   False,
        }
        if json_format:
            body["format"] = "json"
        resp = requests.post(f"{endpoint}/api/chat", json=body, timeout=timeout)
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()

    # LM Studio — OpenAI-compatible
    body = {
        "model":       model,
        "temperature": temp,
        "messages":    messages,
        "stream":      False,
    }
    if json_format:
        body["response_format"] = {"type": "json_object"}
    resp = requests.post(f"{endpoint}/v1/chat/completions", json=body, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate(prompt: str, config: dict, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Send a generation request. Returns the generated text as a string."""
    provider = config.get("provider", "lmstudio")
    model    = config.get("model", "gemma-4-27b-it")
    temp     = config.get("temperature", 0.8)
    endpoint = _endpoint(config)

    if provider == "ollama":
        body = {
            "model":   model,
            "prompt":  prompt,
            "options": {"temperature": temp},
            "think":   config.get("think", False),
            "stream":  False,
        }
        resp = requests.post(f"{endpoint}/api/generate", json=body, timeout=timeout)
        resp.raise_for_status()
        return resp.json()["response"].strip()

    # LM Studio: wrap prompt as a user chat message
    body = {
        "model":       model,
        "temperature": temp,
        "messages":    [{"role": "user", "content": prompt}],
        "stream":      False,
    }
    resp = requests.post(f"{endpoint}/v1/chat/completions", json=body, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def provider_label(config: dict) -> str:
    """Human-readable provider name for display."""
    return "LM Studio" if config.get("provider", "lmstudio") == "lmstudio" else "Ollama"
