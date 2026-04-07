from src.domain.models.email import DraftEmail


def build_refinement_prompt(draft: DraftEmail, hint: str | None = None) -> str:
    lines = [
        "You are a strict validator and editor — NOT a writer.",
        "",
        "Draft to refine:",
        f"Subject: {draft.subject}",
        f"Body: {draft.body}",
        "",
        "Your responsibilities:",
        "- Fix structure and remove redundancy.",
        "- Enforce length limits.",
        "- Ensure clarity without adding new content.",
        "",
        "Strict rules:",
        "- Do NOT add new ideas.",
        "- Do NOT expand the email.",
        "- Do NOT improve by making it longer.",
        "- REMOVE non-essential content.",
        "",
        "Hard length constraints:",
        "- body must be between 100 and 1500 characters.",
        "- If above 1500 characters: you MUST reduce.",
        "- If below 100 characters: you MUST expand.",
        "- subject must be between 5 and 150 characters.",
        "",
        "Output ONLY valid JSON — no markdown, no explanation, no extra keys:",
        '{"subject": "string", "body": "string"}',
        "",
        "Before returning, verify: body length is within bounds, no extra keys, body is plain text, output is valid JSON.",
    ]

    if hint is not None:
        lines.append("")
        lines.append(hint)

    return "\n".join(lines)
