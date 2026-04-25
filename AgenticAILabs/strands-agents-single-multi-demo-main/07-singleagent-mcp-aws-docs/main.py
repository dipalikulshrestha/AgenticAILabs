"""
AWS Documentation Agent - Main Entry Point
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the MCP client and agent creation function
from agents.agent import stdio_mcp_client, create_agent

async def main():
    """Main entry point for the agent"""
    print("🚀 Starting AWS Documentation Agent...")
    
    try:
        # Initialize the agent within MCP context
        with stdio_mcp_client:
            # Get the tools from the MCP server
            tools = stdio_mcp_client.list_tools_sync()
            
            # Create an agent with these tools
            agent = create_agent(tools)
            
            print("✅ Agent initialized successfully!")
            print("💬 You can now ask questions about AWS documentation.")
            print("📝 Type 'exit' or 'quit' to stop the agent.")
            print("🔄 Streaming is enabled - responses will be streamed in real-time.")
            print()
            
            # Interactive loop
            while True:
                try:
                    user_input = input("👤 You: ")
                    
                    if user_input.lower() in ['exit', 'quit', 'bye']:
                        print("👋 Goodbye!")
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    print("🤖 Agent is thinking...")
                    
                    # Handle streaming response
                    print("🔄 Streaming response:")
                    agent_stream = agent.stream_async(user_input)
                    async for event in agent_stream:
                        if hasattr(event, 'data'):
                            print(event.data, end='', flush=True)
                        elif hasattr(event, 'current_tool_use') and event.current_tool_use.get('name'):
                            print(f"\n🔧 USING TOOL: {event.current_tool_use['name']}")
                    print()  # New line after streaming
                    
                    print()
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    print("🔄 Please try again.")
                    print()
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)