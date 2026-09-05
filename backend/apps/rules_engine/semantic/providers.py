"""
Local LLM Provider Abstraction for Legal Metrology Semantic Evaluation.

Supports cloud LLM providers.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def evaluate_semantic_rule(
        self,
        rule_id: str,
        section_ref: str,
        statutory_requirement: str,
        candidate_text: str,
        field_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Submits a semantic classification prompt to the LLM.

        Returns a dictionary adhering to the required schema:
        {
            "rule_id": str,
            "status": "PASS" | "FAIL" | "WARNING" | "REVIEW",
            "confidence": float (0.0 - 1.0),
            "evidence": str (text actually present in OCR),
            "reason": str,
            "requires_human_review": bool
        }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider service is reachable and ready."""
        pass





class OpenRouterProvider(BaseLLMProvider):
    """
    Cloud LLM provider communicating via OpenRouter's HTTP REST API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        self.model = model or getattr(settings, "OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")
        self.api_key = api_key or getattr(settings, "OPENROUTER_API_KEY", "")
        self.timeout = float(timeout or getattr(settings, "LLM_TIMEOUT_SECONDS", 30.0))

    def is_available(self) -> bool:
        """Returns True if API key is configured."""
        return bool(self.api_key)

    def build_prompt(
        self,
        rule_id: str,
        section_ref: str,
        statutory_requirement: str,
        candidate_text: str,
        field_name: str,
    ) -> tuple[str, str]:
        system_prompt = (
            "You are an auxiliary legal metrology compliance analyzer. "
            "Your sole task is semantic interpretation of ambiguous package text against statutory rules.\n\n"
            "STRICT CONSTRAINTS:\n"
            "1. Output MUST be ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "rule_id": string,\n'
            '  "status": "PASS" | "FAIL" | "WARNING" | "REVIEW",\n'
            '  "confidence": number between 0.0 and 1.0,\n'
            '  "evidence": string (MUST be verbatim or exact text present in the Candidate Text),\n'
            '  "reason": string,\n'
            '  "requires_human_review": boolean\n'
            "}\n"
            "2. DO NOT invent or assume facts. Evidence MUST come directly from Candidate Text.\n"
            "3. If the Candidate Text is ambiguous, unclear, or inconclusive, return status: 'REVIEW' with requires_human_review: true.\n"
            "4. NEVER attempt numeric math or unit conversion. Only evaluate linguistic semantics.\n"
            "5. OUTPUT ONLY JSON. DO NOT output markdown blocks or any other text before or after the JSON."
        )

        user_content = (
            f"Rule ID: {rule_id}\n"
            f"Section: {section_ref}\n"
            f"Target Declaration Field: {field_name}\n"
            f"Statutory Requirement: {statutory_requirement}\n"
            f"Candidate Text from Package: \"{candidate_text}\"\n\n"
            "Evaluate whether the Candidate Text semantically satisfies the statutory requirement."
        )

        return system_prompt, user_content

    def evaluate_semantic_rule(
        self,
        rule_id: str,
        section_ref: str,
        statutory_requirement: str,
        candidate_text: str,
        field_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not candidate_text or not candidate_text.strip():
            return {
                "rule_id": rule_id,
                "status": "REVIEW",
                "confidence": 0.0,
                "evidence": "",
                "reason": "No candidate text available for semantic analysis.",
                "requires_human_review": True,
            }

        if not self.is_available():
            return {
                "rule_id": rule_id,
                "status": "REVIEW",
                "confidence": 0.0,
                "evidence": "",
                "reason": "OpenRouter API Key not configured.",
                "requires_human_review": True,
            }

        system_prompt, user_content = self.build_prompt(
            rule_id=rule_id,
            section_ref=section_ref,
            statutory_requirement=statutory_requirement,
            candidate_text=candidate_text,
            field_name=field_name,
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "SIH-2026-App",
            "Content-Type": "application/json"
        }

        chat_url = f"{self.base_url}/chat/completions"
        try:
            resp = requests.post(chat_url, json=payload, headers=headers, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(
                    "OpenRouter API returned HTTP %s for rule %s: %s",
                    resp.status_code,
                    rule_id,
                    resp.text[:150],
                )
                return {
                    "rule_id": rule_id,
                    "status": "REVIEW",
                    "confidence": 0.0,
                    "evidence": "",
                    "reason": f"OpenRouter API error {resp.status_code}.",
                    "requires_human_review": True,
                }

            response_data = resp.json()
            message_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Clean up markdown blocks if the model ignored the system prompt
            if message_content.startswith("```json"):
                message_content = message_content[7:]
            if message_content.startswith("```"):
                message_content = message_content[3:]
            if message_content.endswith("```"):
                message_content = message_content[:-3]
                
            parsed = json.loads(message_content.strip())
            return parsed

        except requests.exceptions.Timeout:
            logger.warning("OpenRouter API timed out (%ss) for rule %s", self.timeout, rule_id)
            return {
                "rule_id": rule_id,
                "status": "REVIEW",
                "confidence": 0.0,
                "evidence": "",
                "reason": f"Semantic evaluation timed out after {self.timeout}s.",
                "requires_human_review": True,
            }
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            logger.info("OpenRouter is unreachable (%s); falling back to REVIEW for rule %s", e, rule_id)
            return {
                "rule_id": rule_id,
                "status": "REVIEW",
                "confidence": 0.0,
                "evidence": "",
                "reason": "OpenRouter API is unreachable.",
                "requires_human_review": True,
            }
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("OpenRouter returned invalid JSON for rule %s: %s", rule_id, e)
            return {
                "rule_id": rule_id,
                "status": "REVIEW",
                "confidence": 0.0,
                "evidence": "",
                "reason": "Invalid JSON response returned by LLM.",
                "requires_human_review": True,
            }


def get_llm_provider() -> Optional[BaseLLMProvider]:
    """Factory creating the configured LLM provider."""
    provider_name = getattr(settings, "LLM_PROVIDER", "openrouter").lower()
    if provider_name == "openrouter":
        return OpenRouterProvider()
    logger.warning("Unsupported LLM_PROVIDER '%s', defaulting to None", provider_name)
    return None
