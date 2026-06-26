import json
import re
from typing import Any, Dict, Optional

from tenacity import retry, stop_after_attempt, wait_fixed

from app.llm.provider import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str],
        model: str,
        temperature: float,
        timeout_seconds: int,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed. Run: pip install -r requirements.txt") from exc

        kwargs: Dict[str, Any] = {
            "api_key": api_key,
            "timeout": timeout_seconds,
        }
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model
        self.temperature = temperature

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": "json_schema", "json_schema": json_schema},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("LLM returned empty content")
            return json.loads(self._clean_json_content(content))
        except Exception as exc:
            raise RuntimeError(f"OpenAI-compatible LLM JSON generation failed: {exc}") from exc

    def _clean_json_content(self, content: str) -> str:
        text = content.strip()
        # 部分兼容模型即使要求 JSON，也可能包一层 Markdown 代码块，这里做最小清洗。
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else text
