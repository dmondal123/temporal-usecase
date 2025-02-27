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
    You are a merchant assistant for Amazon, managing purchase requests and providing Tailored payment options.
    Your cars responsibilities:
    Process purchase Intants fras Consumer agents.
    Communicate with Issuer agents for Apply optimal payment options (EMI, PL, cashback, trade-ini. product details and availability.
    """
    
    agent = BaseAgent(
        user_id=user_id,
        system_message=system_message,
        agents=colleague_agents,
        agent_type="merchant"
    )

    try:
        loop.run_until_complete(agent.start_worker(interrupt_event = interrupt_event))
    except KeyboardInterrupt:
        print("Interrupt received, exiting...")
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())