TEST_DELIVERY_MAP: dict[str, int] = {
    "Sales Technology": 1,
    "Marketing Automation": 101,
    "AI / ML Platforms": 47,
    "Fintech": 66,
    "DevOps / Infrastructure": 85,
}


def should_deliver(mode: str, lead_id: int, industry: str | None, email: str | None) -> bool:
    if not email:
        return False
    if mode == "REAL":
        return True
    if mode == "TEST":
        if industry is None:
            return False
        return TEST_DELIVERY_MAP.get(industry) == lead_id
    return False
