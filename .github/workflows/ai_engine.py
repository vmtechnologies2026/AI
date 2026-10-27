import httpx
from .config import settings

SYSTEM_PROMPTS = {
    "chat": "You are JVM AI, a helpful assistant created for JVM Technologies. Be accurate, clear, and transparent when uncertain.",
    "code": "You are JVM Code Assistant. Help write, explain, review, and debug code. Use readable code blocks and explain important choices. Never claim code was executed unless it actually was."
}

async def generate_reply(messages: list[dict], mode: str = "chat") -> str:
    provider = settings.ai_provider.strip().lower()
    system_message = {"role": "system", "content": SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])}
    history = [system_message] + messages[-20:]

    timeout = httpx.Timeout(settings.ai_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider == "ollama":
            base = settings.ai_base_url.rstrip("/")
            # Ollama's native chat API does not require a key.
            response = await client.post(
                f"{base}/api/chat",
                json={"model": settings.ai_model, "messages": history, "stream": False}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip() or "The model returned an empty response."
        elif provider in ("openai_compatible", "openai"):
            base = settings.ai_base_url.rstrip("/")
            headers = {}
            if settings.ai_api_key:
                headers["Authorization"] = f"Bearer {settings.ai_api_key}"
            response = await client.post(
                f"{base}/chat/completions",
                headers=headers,
                json={"model": settings.ai_model, "messages": history, "temperature": 0.7}
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise RuntimeError("Unsupported AI_PROVIDER. Use 'ollama' or 'openai_compatible'.")
