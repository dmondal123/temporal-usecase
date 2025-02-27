import sys
import asyncio
from framework.BaseAgent import BaseAgent

interrupt_event = asyncio.Event()
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    user_id = sys.argv[1]
    loop = asyncio.new_event_loop()
    colleague_agents = {
        "HDFCBank": {
            'type': 'Issuer',
            'about': 'HDFC Bank communic municates with merchants to find products and create pay roate payment plans for consumers'
        },
        "ICICIBank": {
            'type': 'Issuer',
            'about': 'ICICI Bank comunicates with merchants to find products and create payment plans for consumers'
        }
    }

    system_message = f"""
    You are a dedicated personal shopping assistant for (user_id).
    This includes handling all communication with bank agents, collecting quotes, summarizing and ranking d asi payment plans and finally showing them to your user/operator.
    - All messages must be through the tool call response
    - when you are communicating with bank agents, they know that you are an Al assistant 
    - Contact bank & agents to send purchase and discount detalls, 
    - Rank offers based on the best terms and remove duplicate offers from different banks.
    - Only notify usar/operator of final results when or if you need guidance. 
    - When you are messaging any agents, the communication should be concise and straightforward with all compelling way. Always include the forestt ing. purchase Link,
    - use markdown features like strikethrough and emojis to the required sarkdown straightforward with all compelling way. Always include the forestt ing. purchase Link,
    """

    agent = BaseAgent(
        user_id=user_id,
        system_message=system_message,
        agents=colleague_agents,
        language="Bengali",
        agent_type="consumer"
    )

    try:
        loop.run_until_complete(agent.start_worker(interrupt_event = interrupt_event))
    except KeyboardInterrupt:
        print("Interrupt received, exiting...")
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
