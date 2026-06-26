# ADR-001: Structured Outputs (JSON Schema) for OpenAI-compatible endpoints

## Status
Accepted

## Context
When using OpenAI-compatible local model providers (like LM Studio) with complex reasoning or distilled reasoning models (e.g. DeepSeek-R1), models often output extensive reasoning steps. Enforcing structured output forces the model to restrict its final response to a JSON object matching a strict schema, bypassing reasoning output formatting issues.

## Decision
We implemented a setting `lar_openai_json_schema` which, when enabled, injects the `response_format` JSON Schema parameter into the `call_openai()` body payload:
- Schema requests a JSON object matching `{"suggestion": "URL"}`.
- Instructs the system prompt to comply with the schema format.
- Disables API key enforcement for custom base URLs, supporting local endpoints.

## Consequences
- Guarantees format compliance at the API layer for supported models.
- Prevents structural parse errors during model responses.
