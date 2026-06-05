"""OpenRouter-backed contextual assessor.

OpenRouter exposes an OpenAI-compatible chat-completions API, a different wire format from
the Anthropic SDK, so this is a separate backend rather than a base-url tweak of
``LLMAssessor``. It speaks raw HTTP via the standard library to keep the repo
dependency-free, reuses the same cached rubric and the same JSON->ContextAssessment
coercion, and keeps the deterministic hard floor. Any model on OpenRouter works; the
default is a current Claude model.

    from ai_safety_os import OpenRouterAssessor
    assessor = OpenRouterAssessor()                 # reads OPENROUTER_API_KEY
    assessor = OpenRouterAssessor("anthropic/claude-opus-4.8")
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from ai_safety_os.floor import ConstitutionFloor
from ai_safety_os.llm_assessor import (
    SYSTEM_RUBRIC,
    LLMAssessorError,
    _render_scenario,
    assessment_from_payload,
)
from ai_safety_os.reward_hacking import RewardHackingDetector
from ai_safety_os.schema import ContextAssessment, Scenario

DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# OpenRouter cannot enforce the Anthropic tool schema, so the shape is specified in the
# prompt and the response is parsed and clamped on our side.
JSON_INSTRUCTION = (
    "Respond with ONLY a single minified JSON object and nothing else (no prose, no code "
    "fences). Keys, all required: situation (string), role_authority (number 0-1), stakes "
    "(number 0-1), reversibility (number 0-1), privacy_sensitivity (number 0-1), "
    "norm_conflict (number 0-1), confidence (number 0-1), universalizability (number 0-1), "
    "stakeholders (array of strings), reward_hacking_signals (array of strings), "
    "rationale (string)."
)


class OpenRouterAssessorError(LLMAssessorError):
    """Raised when an OpenRouter assessment cannot be produced."""


class OpenRouterAssessor:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        max_tokens: int = 2000,
        timeout: float = 90.0,
        max_retries: int = 3,
        use_json_mode: bool = True,
        floor: ConstitutionFloor | None = None,
        reward_hacking: RewardHackingDetector | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_json_mode = use_json_mode
        self.floor = floor or ConstitutionFloor()
        self.reward_hacking = reward_hacking or RewardHackingDetector()
        self.calls = 0
        # Cost/latency instrumentation, populated per call.
        self.last_latency_s = 0.0
        self.last_usage: dict[str, Any] = {}
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    @staticmethod
    def available(api_key: str | None = None) -> bool:
        return bool(api_key or os.environ.get("OPENROUTER_API_KEY"))

    def assess(self, scenario: Scenario) -> ContextAssessment:
        floor_violations = self.floor.check(scenario)
        keyword_signals = self.reward_hacking.detect(scenario)
        parsed = self._call(scenario)
        return assessment_from_payload(
            scenario, parsed, floor_violations, keyword_signals
        )

    def _call(self, scenario: Scenario) -> dict[str, Any]:
        if not self.api_key:
            raise OpenRouterAssessorError(
                "Set OPENROUTER_API_KEY (or pass api_key=) to use the OpenRouter assessor."
            )
        prompt = f"{_render_scenario(scenario)}\n\n{JSON_INSTRUCTION}"
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_RUBRIC},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.max_tokens,
        }
        if self.use_json_mode:
            body["response_format"] = {"type": "json_object"}

        # Retry a parse failure once: a model occasionally returns an empty or non-JSON
        # message, and a fresh sample usually parses. Keeps long benchmark runs from
        # aborting on a single bad response.
        last_error: OpenRouterAssessorError | None = None
        for _ in range(2):
            content = self._post(dict(body))
            try:
                return _extract_json(content)
            except OpenRouterAssessorError as exc:
                last_error = exc
        raise last_error if last_error else OpenRouterAssessorError("No response.")

    def _post(self, body: dict[str, Any]) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter attribution headers (optional but polite).
            "HTTP-Referer": "https://github.com/kalyvask/ai-safety-os",
            "X-Title": "AI Safety OS",
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            request = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
            )
            try:
                start = time.monotonic()
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                self.last_latency_s = time.monotonic() - start
                self.last_usage = data.get("usage") or {}
                self.total_prompt_tokens += self.last_usage.get("prompt_tokens", 0) or 0
                self.total_completion_tokens += (
                    self.last_usage.get("completion_tokens", 0) or 0
                )
                self.calls += 1
                return _message_content(data)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:300]
                # Retry transient server/rate errors; fail fast on client errors.
                if exc.code in (429, 500, 502, 503, 529) and attempt < self.max_retries - 1:
                    last_error = OpenRouterAssessorError(f"HTTP {exc.code}: {detail}")
                    time.sleep(2 ** attempt)
                    continue
                # If JSON mode is rejected, retry once without it.
                if exc.code == 400 and "response_format" in body:
                    body = {k: v for k, v in body.items() if k != "response_format"}
                    last_error = OpenRouterAssessorError(f"HTTP 400: {detail}")
                    continue
                raise OpenRouterAssessorError(f"HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise OpenRouterAssessorError(f"OpenRouter request failed: {exc}") from exc
        raise OpenRouterAssessorError(f"OpenRouter request failed: {last_error}")


def _message_content(data: dict[str, Any]) -> str:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterAssessorError(f"Unexpected response shape: {data}") from exc
    content = message.get("content")
    if isinstance(content, list):  # some providers return content parts
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    if not content:
        raise OpenRouterAssessorError("Empty response content.")
    return content


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        fenced = text.split("```")
        text = fenced[1] if len(fenced) > 1 else text
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip().strip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the first decodable JSON object anywhere in the text.
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char == "{":
            try:
                obj, _ = decoder.raw_decode(text[index:])
                return obj
            except json.JSONDecodeError:
                continue
    raise OpenRouterAssessorError("No JSON object found in model response.")
