"""
Test Agent v2 - Agent Definition
Description: Test agent
"""

import os
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time, calculator
from tools.create_appointment import create_appointment
from tools.list_appointments import list_appointments
from tools.update_appointment import update_appointment

# Model Configuration Constants

MODEL_ID = "arn:aws:bedrock:us-east-1:167771397877:inference-profile/us.amazon.nova-2-lite-v1:0"
MODEL_REGION = "us-east-1"
MODEL_TEMPERATURE = 1
MODEL_MAX_TOKENS = 8192
MODEL_TOP_P = 1
MODEL_STREAMING = True
MODEL_STOP_SEQUENCES = ["exit"]

# Model Configuration
model = BedrockModel(
    model_id=MODEL_ID,
    region=MODEL_REGION,
    temperature=MODEL_TEMPERATURE,
    max_tokens=MODEL_MAX_TOKENS,
    top_p=MODEL_TOP_P,
    streaming=MODEL_STREAMING,
    stop_sequences=MODEL_STOP_SEQUENCES,

)

# Agent Instance
test_agent_v2_agent = Agent(
    system_prompt="You are an receptionist. Your task is to create, manage appointments of the users. Ask relevant questions to create the appointment and ask for double confirmation before you delete any appointment. ",
    model=model,
    tools=[current_time, calculator, create_appointment, list_appointments, update_appointment],
    name="Test Agent v2",
    description="Test agent"
)