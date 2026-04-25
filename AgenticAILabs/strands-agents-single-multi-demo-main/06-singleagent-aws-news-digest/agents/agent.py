"""
Test Agent v2 - Agent Definition
Description: Test agent
"""

import os
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import rss, http_request


rss_feeds = [ { "title" : "What's new with AWS?",
 "rss" : "https://aws.amazon.com/about-aws/whats-new/recent/feed/"   
}, 
{
    "title" : "Dev.to Heroes Blogs",
    "link" : "https://dev.to/aws-heroes"
},]

# Model Configuration Constants

MODEL_ID = "arn:aws:bedrock:us-east-1:167771397877:inference-profile/us.amazon.nova-2-lite-v1:0"
MODEL_REGION = "us-east-1"
MODEL_TEMPERATURE = 1
MODEL_MAX_TOKENS = 8192
MODEL_TOP_P = 1
MODEL_STREAMING = True
MODEL_STOP_SEQUENCES = ["exit"]
SYSTEM_PROMPT = f"You are an AWS News Digest Agent. Your task is to fetch the latest news articles from the RSS feeds listed in {rss_feeds} using the available tools (rss, http_request). For each article, generate a concise summary that includes the title (as a hyperlink to the URL), the author's name if available, and a 2–3 sentence factual summary of the content. Ensure that all outputs are accurate, objective, and derived strictly from the source material. Do not include personal opinions, speculations, or fabricated information. Maintain a clean Markdown format. If no valid articles are found, respond with: 'No new articles available at the moment.' "


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
    system_prompt=SYSTEM_PROMPT,
    model=model,
    tools=[rss, http_request],
    name="Test Agent v2",
    description="Test agent"

)