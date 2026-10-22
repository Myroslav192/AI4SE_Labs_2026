"""OpenAI Structured Outputs with content-addressed caching and an audit trail."""
import hashlib
import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


class AgentClient:
    def __init__(self, output: Path, max_calls: int = 150, api_mode: str = "responses"):
        if not os.getenv("OPENAI_API_KEY", "").strip():
            raise ValueError("OPENAI_API_KEY is missing. Add it to the project .env file.")
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
        self.client = OpenAI(base_url=base_url, timeout=600.0, max_retries=2)
        self.api_mode, self.max_calls, self.calls = api_mode, max_calls, 0
        self.output = output
        self.cache = output / "cache"
        self.events: list[dict] = []
        self._lock = threading.RLock()
        output.mkdir(parents=True, exist_ok=True)

    def invoke(self, role: str, model: str, prompt: str, payload: dict,
               schema: type[T], max_tokens: int = 12000) -> T:
        request = dict(model=model, prompt=prompt, payload=payload, schema=schema.model_json_schema(),
                       api_mode=self.api_mode, endpoint=str(self.client.base_url), max_tokens=max_tokens)
        digest = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        cache_path = self.cache / f"{digest}.json"
        event = dict(time_utc=datetime.now(timezone.utc).isoformat(), role=role, requested_model=model,
                     request_hash=digest, schema=schema.__name__)
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            result = schema.model_validate(cached["output"])
            event.update(status="cache_hit", served_model=cached["served_model"], input_tokens=0, output_tokens=0)
            self._record(event)
            return result
        with self._lock:
            if self.calls >= self.max_calls:
                raise RuntimeError(f"API call limit ({self.max_calls}) reached; cached work is preserved.")
            self.calls += 1
        started = time.monotonic()
        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
        try:
            if self.api_mode == "responses":
                response = self.client.responses.parse(model=model, input=messages, text_format=schema,
                                                       max_output_tokens=max_tokens, store=False)
                if response.status != "completed" or response.output_parsed is None:
                    raise RuntimeError("Model refused or returned incomplete structured output.")
                result = response.output_parsed
                usage = response.usage
                input_tokens = usage.input_tokens if usage else 0
                output_tokens = usage.output_tokens if usage else 0
            else:
                response = self.client.chat.completions.parse(model=model, messages=messages,
                                                             response_format=schema, max_completion_tokens=max_tokens)
                result = response.choices[0].message.parsed
                if result is None:
                    raise RuntimeError("Model refused or returned no structured output.")
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0
        except Exception as exc:
            event.update(status="failed", error_type=type(exc).__name__, status_code=getattr(exc, "status_code", None))
            self._record(event)
            # API exception messages can contain credential fragments; do not print them.
            raise RuntimeError(f"{role}: API request failed ({type(exc).__name__}, HTTP "
                               f"{getattr(exc, 'status_code', 'n/a')}). Check key, endpoint, model access, "
                               "credits or output-token limit. See run_trace.jsonl for safe metadata.") from None
        event.update(status="completed", served_model=response.model, response_id=response.id,
                     input_tokens=input_tokens, output_tokens=output_tokens,
                     elapsed_seconds=round(time.monotonic() - started, 2))
        with self._lock:
            write_json(cache_path, dict(served_model=response.model, output=result.model_dump(),
                                       input_tokens=input_tokens, output_tokens=output_tokens, response_id=response.id))
        self._record(event)
        return result

    def _record(self, event: dict) -> None:
        with self._lock:
            self.events.append(event)
            with (self.output / "run_trace.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        print(f"[{event['role']}] {event['requested_model']}: {event['status']}", flush=True)

    def close(self) -> None:
        self.client.close()
