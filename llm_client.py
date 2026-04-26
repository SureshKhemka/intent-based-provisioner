"""
LLM provider abstraction — supports LM Studio (OpenAI-compat) and Ollama.

Provider is selected via config["provider"]: "lmstudio" (default) or "ollama".

  chat(messages, config)     — for classify / judge (structured JSON responses)
  generate(prompt, config)   — for free-form text generation (test case generation)
"""

import requests

DEFAULT_TIMEOUT = 120


def _strip_json(text: str) -> str:
    """Remove markdown code fences and leading/trailing whitespace."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop opening fence line (```json or ```)
        lines = lines[1:]
        # Drop closing fence if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _endpoint(config: dict) -> str:
    if config.get("provider", "lmstudio") == "ollama":
        return config.get("ollama_endpoint", "http://localhost:11434")
    return config.get("lmstudio_endpoint", "http://localhost:1234")


def chat(messages: list, config: dict, json_format: bool = True, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Send a chat request. Returns the assistant message content as a string."""
    provider = config.get("provider", "lmstudio")
    model    = config.get("model", "gemma-4-26b-a4b-it-mlx")
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
    # Note: response_format json_object is omitted — not all LM Studio builds support it.
    # The system prompt instructs the model to respond with JSON, which is sufficient.
    body = {
        "model":       model,
        "temperature": temp,
        "messages":    messages,
        "stream":      False,
    }
    resp = requests.post(f"{endpoint}/v1/chat/completions", json=body, timeout=timeout)
    if not resp.ok:
        raise RuntimeError(
            f"LM Studio returned {resp.status_code}: {resp.text[:200]}"
        )
    content = resp.json()["choices"][0]["message"]["content"]
    return _strip_json(content) if json_format else content.strip()


def generate(prompt: str, config: dict, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Send a generation request. Returns the generated text as a string."""
    provider = config.get("provider", "lmstudio")
    model    = config.get("model", "gemma-4-26b-a4b-it-mlx")
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
    if not resp.ok:
        raise RuntimeError(
            f"LM Studio returned {resp.status_code}: {resp.text[:200]}"
        )
    return resp.json()["choices"][0]["message"]["content"].strip()


def provider_label(config: dict) -> str:
    """Human-readable provider name for display."""
    return "LM Studio" if config.get("provider", "lmstudio") == "lmstudio" else "Ollama"
