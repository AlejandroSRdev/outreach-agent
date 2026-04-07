# AI Integration

AI is used in 2 of 3 pipeline stages. It is treated as a non-deterministic, untrusted external dependency.

---

## Where AI Is Used

| Stage      | AI Used | Purpose                          |
|------------|--------|----------------------------------|
| Research   | No     | Deterministic DB read           |
| Generation | Yes    | Produce draft message           |
| Refinement | Yes    | Improve and structure output    |

---

## Model Strategy

A single model is used for both stages:

- Model: gpt-4o-mini

Different behavior is controlled via prompting and temperature:

- Generation → higher creativity
- Refinement → low temperature, strict output

---

## Input Contract (per AI call)

AI receives a **system-constructed prompt**. Raw user input is never passed unprocessed.

### Generation prompt includes:

- Lead: name, role  
- Company: industry, description, product, value_proposition, target_market, recent_activity (if present), strategic_focus  
- Tone instruction: `professional`  

### Refinement prompt includes:

- All of the above  
- Draft message (subject, body)  
- Instruction: improve clarity, tone, and enforce structure  
- Explicit JSON schema definition  

---

## Output Contract

### Generation Output (non-structured)


{
  subject : str
  body : str
}


- No strict schema enforcement beyond presence of both fields
- No lists or structured metadata generated at this stage

---

### Refinement Output (final structured output)

AI must return a **valid JSON object** conforming to:


{
  subject : str [5–150 chars]
  body : str [100–1500 chars]
}

---

## Validation Strategy

Validation is applied **only after the refinement stage**, before persistence.

Steps:

1. Parse response as JSON — fail if unparseable  
2. Validate against `FinalMessage` schema — fail if any field is missing, wrong type, or violates constraints  
3. Verify `tone == "professional"` — fail if not  
4. Compute `word_count` from `body` — system-owned  

Validation is binary:
- pass → continue  
- fail → retry or abort  

No silent correction. No partial acceptance.

---

## Failure Handling

| Failure                      | Retry eligible | Action                                 |
|-----------------------------|---------------|----------------------------------------|
| AI timeout                  | Yes           | Retry up to 2 times                    |
| Unparseable JSON            | Yes           | Retry up to 2 times                    |
| Schema validation failure   | Yes           | Retry up to 2 times                    |
| Max retries exceeded        | No            | Stage fails, pipeline halts            |

Additional rules:

- Prompt is identical on retry  
- Each attempt is logged with:
  - attempt number
  - failure reason
  - raw output (truncated to 2000 chars)  
- Only the final result is persisted to `pipeline_stage_results`  

---

## Trust Model

- AI is an external, non-deterministic dependency  
- The system owns correctness — AI owns generation only  
- Every output is untrusted until validated  
- The backend controls:
  - schema enforcement  
  - acceptance  
  - persistence  
