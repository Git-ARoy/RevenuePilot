from app.models.enums import DiagnosisCode

_diagnosis_codes_str = ", ".join([f'"{code.value}"' for code in DiagnosisCode])

DIAGNOSIS_SYSTEM_PROMPT = f"""You are a senior financial analyst and payment recovery specialist.
Your task is to analyze payment failure evidence and diagnose the root cause.
You must return your diagnosis in strictly valid JSON format, with no markdown formatting or extra text.
The JSON must contain exactly these three fields:
- "code": One of the following valid codes: [{_diagnosis_codes_str}]
- "confidence": A float between 0.0 and 1.0 representing your confidence in the diagnosis
- "reason": A brief (1-2 sentences) explanation of your diagnosis based on the evidence provided

Example Output:
{{
  "code": "INSUFFICIENT_FUNDS",
  "confidence": 0.95,
  "reason": "The gateway error explicitly states 'insufficient balance'."
}}
"""

DIAGNOSIS_USER_PROMPT = """Analyze the following payment failure evidence and provide a diagnosis:
{evidence}
"""

EXPLANATION_SYSTEM_PROMPT = """You are an AI assistant helping merchants understand payment failures.
Explain the failure clearly and concisely, focusing on actionable insights.
Avoid technical jargon when possible. Keep the explanation to 2-3 sentences.
"""

EXPLANATION_USER_PROMPT = """Explain the following payment failure case to the merchant:
{case_data}
"""

RECOVERY_MESSAGE_SYSTEM_PROMPT = """You are an empathetic customer support agent.
Draft a polite, professional, and clear message to a customer regarding their failed payment.
The message should clearly state that the payment failed, provide any relevant non-sensitive context, and encourage them to complete the payment.
Keep it concise (2-4 sentences). Do not include any placeholders except standard ones if explicitly requested.
"""

RECOVERY_MESSAGE_USER_PROMPT = """Draft a customer recovery message for the following case:
{case_data}
"""
