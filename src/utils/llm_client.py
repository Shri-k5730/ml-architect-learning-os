from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_CONFIG_PATH = PROJECT_ROOT / "config" / "model_config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class LLMClientError(Exception):
    """Raised when LLM client setup or invocation fails."""


def load_model_config() -> Dict[str, Any]:
    if not MODEL_CONFIG_PATH.exists():
        raise LLMClientError(f"Model config not found: {MODEL_CONFIG_PATH}")

    with MODEL_CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise LLMClientError("model_config.yaml must contain a top-level object.")

    return data


def get_provider_name_for_agent(agent_name: str, model_config: Dict[str, Any]) -> str:
    agent_map = model_config.get("agent_model_map", {})
    provider_name = agent_map.get(agent_name)

    if not provider_name:
        provider_name = model_config.get("active_provider")

    if not provider_name:
        raise LLMClientError(f"No provider configured for agent '{agent_name}'.")

    return provider_name


def build_llm_callable(agent_name: str):
    model_config = load_model_config()
    provider_name = get_provider_name_for_agent(agent_name, model_config)
    providers = model_config.get("providers", {})
    provider_cfg = providers.get(provider_name)

    if not provider_cfg:
        raise LLMClientError(f"Provider '{provider_name}' is not defined in model_config.yaml.")

    if not provider_cfg.get("enabled", False):
        raise LLMClientError(f"Provider '{provider_name}' is disabled in model_config.yaml.")

    if provider_name == "openai":
        return build_openai_callable(provider_cfg)

    if provider_name == "tinyllama":
        raise LLMClientError(
            "TinyLlama provider is not wired yet. Start with OpenAI first."
        )

    raise LLMClientError(f"Unsupported provider: {provider_name}")


def extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        raise LLMClientError("OpenAI response did not contain usable text output.")

    texts: list[str] = []

    for item in output:
        item_type = getattr(item, "type", None)
        if item_type != "message":
            continue

        contents = getattr(item, "content", None)
        if not isinstance(contents, list):
            continue

        for content in contents:
            content_type = getattr(content, "type", None)
            text = getattr(content, "text", None)
            if content_type == "output_text" and isinstance(text, str) and text.strip():
                texts.append(text.strip())

    if texts:
        return "\n".join(texts)

    raise LLMClientError("OpenAI response did not contain usable text output.")


def build_openai_callable(provider_cfg: Dict[str, Any]):
    api_key_env = provider_cfg.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env)

    if not api_key:
        raise LLMClientError(
            f"Environment variable '{api_key_env}' is not set. "
            f"Checked .env at {ENV_PATH}"
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMClientError(
            "OpenAI package is not installed. Add it to requirements.txt first."
        ) from exc

    model_name = provider_cfg.get("model")
    temperature = provider_cfg.get("temperature", 0.4)
    max_output_tokens = provider_cfg.get("max_output_tokens", 1200)

    if not model_name:
        raise LLMClientError("OpenAI model name is missing in model_config.yaml.")

    client = OpenAI(api_key=api_key)

    def llm_callable(system_prompt: str, user_prompt: str) -> str:
        if not system_prompt or not user_prompt:
            raise LLMClientError("Both system_prompt and user_prompt are required.")

        try:
            response = client.responses.create(
                model=model_name,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}],
                    },
                ],
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except Exception as exc:
            raise LLMClientError(f"OpenAI call failed: {exc}") from exc

        return extract_response_text(response)

    return llm_callable