from dataclasses import dataclass


@dataclass
class StageConfig:
    model: str
    temperature: float
    max_tokens: int


GENERATION_CONFIG = StageConfig(model="gpt-4o-mini", temperature=0.7, max_tokens=300)
REFINEMENT_CONFIG = StageConfig(model="gpt-4o-mini", temperature=0.3, max_tokens=300)
