"""
Test Agent v2 - Agent Definition
Description: Test agent
"""

import os
from strands import Agent, tool
from strands.models import BedrockModel


# Model Configuration Constants

MODEL_ID = "arn:aws:bedrock:us-east-1:167771397877:inference-profile/global.anthropic.claude-opus-4-6-v1"
MODEL_REGION = "us-east-1"
#MODEL_TEMPERATURE = 1
MODEL_MAX_TOKENS = 8192
MODEL_TOP_P = 1
MODEL_STREAMING = True
MODEL_STOP_SEQUENCES = ["exit"]

# # Guardrails Configuration Constants
# GUARDRAIL_ID = "IDu"
# GUARDRAIL_VERSION = "DRAFT"
# GUARDRAIL_TRACE = "enabled"
# GUARDRAIL_STREAM_PROCESSING_MODE = "sync"
# GUARDRAIL_REDACT_INPUT = True
# GUARDRAIL_REDACT_INPUT_MESSAGE = "[User input redacted.]"
# GUARDRAIL_REDACT_OUTPUT = False
# GUARDRAIL_REDACT_OUTPUT_MESSAGE = "[Assistant output redacted.]"

CACHE_PROMPT_MODE="default"
CACHE_TOOLS_MODE="default"
REASONING_BUDGET_TOKENS=4096


# Model Configuration
model = BedrockModel(
    model_id=MODEL_ID,
    region=MODEL_REGION,
    #temperature=MODEL_TEMPERATURE,
    max_tokens=MODEL_MAX_TOKENS,
    top_p=MODEL_TOP_P,
    streaming=MODEL_STREAMING,
    stop_sequences=MODEL_STOP_SEQUENCES,
    cache_prompt=CACHE_PROMPT_MODE,
    cache_tools=CACHE_TOOLS_MODE,
    additional_request_fields={
        "thinking": {
            "type": "enabled",
            "budget_tokens": REASONING_BUDGET_TOKENS
        }
    },

)



# Agent Instance
test_agent_v2_agent = Agent(
    system_prompt="What is AWS?",
    model=model,
    tools=[],
    name="Test Agent v2",
    description="Test agent",

)