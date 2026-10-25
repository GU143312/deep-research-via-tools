"""Validate structured output without accepting partial or fabricated report data."""

import json
import re

from agents import AgentOutputSchema, ModelBehaviorError


class StructuredOutputError(ModelBehaviorError):
    def __init__(self, stage: str, reason: str):
        self.stage = stage
        self.reason = reason
        super().__init__(f"{stage} output failed validation ({reason}).")


class ResearchOutputSchema(AgentOutputSchema):
    def __init__(self, output_type, stage, diagnostics=None):
        super().__init__(output_type)
        self.stage = stage
        self.diagnostics = diagnostics

    def validate_json(self, json_str):
        # A complete enclosing Markdown fence is presentation, not report content.
        # Never extract a partial object, add missing fields or repair report text.
        fenced = re.fullmatch(r"\s*```(?:json)?\s*\n(.*?)\n```\s*", json_str, re.DOTALL)
        candidate = fenced.group(1) if fenced else json_str
        try:
            value = super().validate_json(candidate)
        except ModelBehaviorError:
            reason = "schema_mismatch"
            try:
                json.loads(candidate)
            except (json.JSONDecodeError, ValueError):
                reason = "invalid_json"
            if self.diagnostics is not None:
                self.diagnostics.append(
                    f"{self.stage}: {reason}; output_characters={len(json_str)}"
                )
            raise StructuredOutputError(self.stage, reason) from None
        if fenced and self.diagnostics is not None:
            self.diagnostics.append(f"{self.stage}: removed enclosing JSON code fence; validated.")
        return value
