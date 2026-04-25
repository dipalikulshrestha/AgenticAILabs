from strands import Agent
from strands_tools import rss, http_request
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

app = BedrockAgentCoreApp()
rss_feeds = [ { "title" : "What's new with AWS?",
 "rss" : "https://aws.amazon.com/about-aws/whats-new/recent/feed/"   
}, 
{
    "title" : "Dev.to Heroes Blogs",
    "link" : "https://dev.to/aws-heroes"
},

]
# Create a Bedrock model instance
bedrock_model = BedrockModel(
    model_id="arn:aws:bedrock:us-east-1:167771397877:inference-profile/us.amazon.nova-2-lite-v1:0",
    region_name='us-east-1',
    temperature=0.3,
)

SYSTEM_PROMPT = f"You are an AWS News Digest Agent. Your task is to fetch the latest news articles from the RSS feeds listed in {rss_feeds} using the available tools (rss, http_request). For each article, generate a concise summary that includes the title (as a hyperlink to the URL), the author's name if available, and a 2–3 sentence factual summary of the content. Ensure that all outputs are accurate, objective, and derived strictly from the source material. Do not include personal opinions, speculations, or fabricated information. Maintain a clean Markdown format. If no valid articles are found, respond with: 'No new articles available at the moment.' "

agent = Agent(model=bedrock_model, system_prompt=SYSTEM_PROMPT, tools=[rss,http_request])
 
@app.entrypoint
def strands_agent_bedrock(payload):
        """
        Invoke the agent with a payload
        """
        user_input = payload.get("prompt")
        print("User input:", user_input)
        response = agent(user_input)
        return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()