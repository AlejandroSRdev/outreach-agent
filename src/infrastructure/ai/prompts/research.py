import json

from src.domain.models.lead import LeadInput


def build_research_prompt(lead: LeadInput) -> str:
    lead_data = json.dumps({"name": lead.name, "company": lead.company, "role": lead.role})
    return f"""You are a research agent that infers structured business context from lead data.

Input:
{lead_data}

Your task is to infer business context about the company and lead based on the provided name, company, and role. Use probabilistic language throughout ("likely", "typically", "may"). Do NOT invent specific facts or hallucinate details you cannot reasonably infer.

Return ONLY valid JSON with this exact structure — no additional text, no explanation:

{{
  "industry": "string or null",
  "description": "string or null",
  "product": "string or null",
  "value_proposition": "string or null",
  "target_market": "string or null",
  "recent_activity": "string or null",
  "strategic_focus": "string or null",
  "additional_context": "string or null"
}}

Rules:
- If you cannot infer a field with reasonable confidence, return null for that field.
- Each non-null field must provide real, specific value — no generic filler.
- Use probabilistic language: "likely", "typically", "may", "appears to".
- Do NOT fabricate specific metrics, dates, or events you cannot reasonably infer.
- Output must be valid JSON only. No markdown, no explanation, no extra keys."""
