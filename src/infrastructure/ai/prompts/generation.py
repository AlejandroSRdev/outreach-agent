from src.domain.models.lead import EnrichedLead


def build_generation_prompt(enriched: EnrichedLead, hint: str | None = None) -> str:
    lines = [
        "You are a senior outbound copywriter specialized in highly personalized B2B outreach.",
        "",
        "Your task is to write a short cold email for a specific lead using only the provided context.",
        "",
        "The objective is to produce a message that feels thoughtful, relevant and commercially intelligent — not generic, not exaggerated, and not obviously AI-written.",
        "",
        "You must infer the most plausible angle of relevance from the lead context and build the email around that angle.",
        "",
        "## Lead data",
        f"Name: {enriched.name}",
        f"Company: {enriched.company}",
    ]

    if enriched.role is not None:
        lines.append(f"Role: {enriched.role}")
    if enriched.industry is not None:
        lines.append(f"Industry: {enriched.industry}")
    if enriched.description is not None:
        lines.append(f"Description: {enriched.description}")
    if enriched.product is not None:
        lines.append(f"Product: {enriched.product}")
    if enriched.value_proposition is not None:
        lines.append(f"Value proposition: {enriched.value_proposition}")
    if enriched.target_market is not None:
        lines.append(f"Target market: {enriched.target_market}")
    if enriched.recent_activity is not None:
        lines.append(f"Recent activity: {enriched.recent_activity}")
    if enriched.strategic_focus is not None:
        lines.append(f"Strategic focus: {enriched.strategic_focus}")
    if enriched.additional_context is not None:
        lines.append(f"Additional context: {enriched.additional_context}")

    lines += [
        "",
        "## Writing objective",
        "Write a short outreach email that:",
        "- feels personalized to this specific lead",
        "- connects the message to the lead's likely context, priorities or workflow",
        "- suggests a relevant AI automation / workflow improvement opportunity",
        "- sounds credible, precise and commercially mature",
        "- creates interest without sounding pushy",
        "",
        "## Constraints",
        "- Do not use generic opening lines such as \"I hope you're doing well\"",
        "- Do not use empty compliments",
        "- Do not invent facts that are not supported by the provided context",
        "- Do not sound like a mass email",
        "- Do not over-explain the product",
        "- Do not use hype, buzzwords or exaggerated claims",
        "- Do not make the email long",
        "",
        "## Style requirements",
        "- Professional, sharp and natural",
        "- Concise but not abrupt",
        "- Specific rather than broad",
        "- Persuasive through relevance, not through pressure",
        "- Written as if by someone who understands operations and workflows",
        "",
        "## Output format",
        "Return plain text only, using this EXACT format — no JSON, no markdown, no extra structure:",
        "",
        "Subject: <subject line here>",
        "",
        "<email body here>",
        "",
        "## Output rules",
        "- Subject must be short and relevant",
        "- Body must be between 100 and 1500 characters. Outputs outside this range are invalid.",
        "- Body must be plain text",
        "- Body must read like a real email",
        "- Body must include a clear but low-pressure closing",
        "- No markdown",
    ]

    if hint is not None:
        lines.append("")
        lines.append(hint)

    return "\n".join(lines)
