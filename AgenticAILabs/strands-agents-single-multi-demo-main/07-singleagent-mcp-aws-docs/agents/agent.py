"""
AWS Documentation Agent - Agent Definition
Description: Agent that uses MCP to access AWS documentation
"""

from strands import Agent
from mcp import StdioServerParameters, stdio_client
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

def create_agent(tools):
    """Create and return the AWS Documentation Agent with provided tools"""
    return Agent(
        model="arn:aws:bedrock:us-east-1:167771397877:inference-profile/us.amazon.nova-2-lite-v1:0",
        tools=tools,
        system_prompt="You are an AWS Documentation Assistant. Use the available AWS documentation tools to provide accurate, up-to-date information about AWS services, pricing, and best practices. Be concise and helpful.",
        name="AWS Documentation Agent",
        description="Agent that provides AWS documentation and information"
    )