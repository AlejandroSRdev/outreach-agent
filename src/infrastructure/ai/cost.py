_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # USD per 1M tokens
}


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = _PRICING.get(model)
    if not pricing:
        return 0.0
    return (input_tokens / 1_000_000) * pricing["input"] + \
           (output_tokens / 1_000_000) * pricing["output"]
