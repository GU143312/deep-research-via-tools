"""Scripted model responses; the Agents SDK and .as_tool() execution remain real."""

import json
from collections import deque
from uuid import uuid4

from agents import Model, ModelResponse
from agents.usage import Usage
from openai.types.responses import (
    Response,
    ResponseCompletedEvent,
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)


def message(text):
    return ResponseOutputMessage(
        id="msg_" + uuid4().hex,
        content=[ResponseOutputText(text=text, type="output_text", annotations=[])],
        role="assistant",
        status="completed",
        type="message",
    )


def tool_call(name, **arguments):
    return ResponseFunctionToolCall(
        name=name, arguments=json.dumps(arguments), call_id=uuid4().hex, type="function_call"
    )


class ScriptedModel(Model):
    def __init__(self, steps):
        self.steps = deque(steps)
        self.calls = []

    async def get_response(
        self,
        system_instructions,
        input,
        model_settings,
        tools,
        output_schema,
        handoffs,
        tracing,
        **kwargs,
    ):
        role, output = self.steps.popleft()
        assert role in system_instructions, (role, system_instructions)
        self.calls.append((role, input, {"tools": tools, **kwargs}))
        return ModelResponse(output=output, usage=Usage(), response_id=uuid4().hex)

    async def stream_response(self, *args, **kwargs):
        result = await self.get_response(*args, **kwargs)
        response = Response(
            id=result.response_id,
            created_at=0,
            model="offline-scripted-model",
            object="response",
            output=result.output,
            parallel_tool_calls=False,
            tool_choice="auto",
            tools=[],
            status="completed",
        )
        yield ResponseCompletedEvent(
            response=response, sequence_number=0, type="response.completed"
        )
