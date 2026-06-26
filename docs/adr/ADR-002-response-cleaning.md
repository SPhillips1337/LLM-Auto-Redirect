# ADR-002: Multi-layered Response Cleaning

## Status
Accepted

## Context
Various providers and reasoning models output thinking/reasoning text before generating their actual response, or wrap JSON responses in markdown blocks. Simple string trims are insufficient and fail `FILTER_VALIDATE_URL`.

## Decision
We implemented a robust cleaning pipeline inside `get_llm_suggestion()` and the call wrappers:
- Increased `max_tokens` to `2048` so reasoning tokens do not cut off output prematurely.
- Fallback check for `reasoning_content` and `thought` fields in completion choices when standard content is empty.
- Strip thinking/thought blocks using regex: `/<(thinking|thought|reasoning)>.*?<\/\\1>/is`.
- Extract raw JSON from markdown wrappers (e.g. ` ```json ... ``` `).
- Try deserializing as JSON to retrieve the `suggestion` key.
- Extract the first valid HTTP/HTTPS URL pattern via regex to handle conversational padding.

## Consequences
- Handles any mixture of reasoning tokens, markdown code blocks, or conversational preambles.
- Supports reasoning models (like DeepSeek-R1, Gemini Thinking) across all providers (Ollama, OpenAI, Gemini, OpenRouter) seamlessly.
