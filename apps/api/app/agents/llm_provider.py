import json
from abc import ABC, abstractmethod
from typing import Optional
import asyncio
import logging

import ollama

from app.core.config import settings
from app.models.enums import DiagnosisCode
from app.agents.prompts import (
    DIAGNOSIS_SYSTEM_PROMPT,
    DIAGNOSIS_USER_PROMPT,
    EXPLANATION_SYSTEM_PROMPT,
    EXPLANATION_USER_PROMPT,
    RECOVERY_MESSAGE_SYSTEM_PROMPT,
    RECOVERY_MESSAGE_USER_PROMPT,
)

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    async def diagnose(self, evidence: dict) -> Optional[dict]:
        """Classify a payment failure. Returns {code, confidence, reason} or None."""
        pass
    
    @abstractmethod
    async def explain(self, case_data: dict) -> str:
        """Generate merchant-facing explanation of a recovery case."""
        pass
    
    @abstractmethod
    async def draft_recovery_message(self, case_data: dict) -> str:
        """Draft a customer-facing recovery message."""
        pass


class MockProvider(LLMProvider):
    """Deterministic provider for testing/simulation. No external calls."""
    
    async def diagnose(self, evidence: dict) -> Optional[dict]:
        error_desc = evidence.get("error_description", "").lower()
        
        if "insufficient" in error_desc or "balance" in error_desc:
            code = DiagnosisCode.INSUFFICIENT_FUNDS
        elif "expired" in error_desc:
            code = DiagnosisCode.EXPIRED_PAYMENT_METHOD
        elif "bank" in error_desc or "declined" in error_desc:
            code = DiagnosisCode.BANK_DECLINE
        elif "timeout" in error_desc or "gateway" in error_desc:
            code = DiagnosisCode.TRANSIENT_GATEWAY_FAILURE
        else:
            code = DiagnosisCode.UNKNOWN_PAYMENT_FAILURE
            
        return {
            "code": code.value,
            "confidence": 0.9,
            "reason": "Mocked diagnosis based on simple keywords"
        }
    
    async def explain(self, case_data: dict) -> str:
        return f"Mock Explanation: Case {case_data.get('id')} failed due to {case_data.get('diagnosis')}."
    
    async def draft_recovery_message(self, case_data: dict) -> str:
        amount = case_data.get("amount", 0) / 100
        return f"Mock Message: Your payment of INR {amount} failed. Please try again using the provided link."


class OllamaProvider(LLMProvider):
    """Local inference via Ollama."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.client = ollama.AsyncClient(host=self.base_url)
        
    async def diagnose(self, evidence: dict) -> Optional[dict]:
        messages = [
            {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
            {"role": "user", "content": DIAGNOSIS_USER_PROMPT.format(evidence=json.dumps(evidence, indent=2))}
        ]
        
        try:
            # Enforce 30s timeout with asyncio.wait_for
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    format='json',
                    options={"temperature": 0.1}
                ),
                timeout=30.0
            )
            
            content = response.get("message", {}).get("content", "")
            if not content:
                logger.error("Empty response from Ollama")
                return None
                
            data = json.loads(content)
            
            # Validate DiagnosisCode
            code_str = data.get("code")
            try:
                DiagnosisCode(code_str)
            except ValueError:
                logger.error(f"Invalid DiagnosisCode returned by LLM: {code_str}")
                return None
                
            return {
                "code": code_str,
                "confidence": float(data.get("confidence", 0.0)),
                "reason": str(data.get("reason", ""))
            }
            
        except asyncio.TimeoutError:
            logger.error("LLM diagnose call timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM diagnose: {str(e)}")
            return None
            
    async def explain(self, case_data: dict) -> str:
        messages = [
            {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
            {"role": "user", "content": EXPLANATION_USER_PROMPT.format(case_data=json.dumps(case_data, indent=2))}
        ]
        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0.4}
                ),
                timeout=30.0
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Error calling LLM explain: {str(e)}")
            return "Unable to generate explanation at this time."
            
    async def draft_recovery_message(self, case_data: dict) -> str:
        messages = [
            {"role": "system", "content": RECOVERY_MESSAGE_SYSTEM_PROMPT},
            {"role": "user", "content": RECOVERY_MESSAGE_USER_PROMPT.format(case_data=json.dumps(case_data, indent=2))}
        ]
        try:
            response = await asyncio.wait_for(
                self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={"temperature": 0.4}
                ),
                timeout=30.0
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Error calling LLM draft_recovery_message: {str(e)}")
            return "Your payment could not be processed. Please try again."


def get_llm_provider() -> LLMProvider:
    """Factory function based on settings.LLM_PROVIDER"""
    if settings.LLM_PROVIDER.lower() == "ollama":
        return OllamaProvider()
    return MockProvider()
