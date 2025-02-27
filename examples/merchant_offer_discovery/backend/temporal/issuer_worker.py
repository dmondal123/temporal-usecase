import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
if project_root not in sys.path:
    sys.path.append(project_root)

import asyncio
from framework.BaseAgent import BaseAgent

interrupt_event = asyncio.Event()
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    user_id = sys.argv[1]
    loop = asyncio.new_event_loop()
    colleague_agents = {
    'Amazon': {'about': "Amazon is an e-commerce platform that sells a variety of products and adds discounts.",
               'type': "Merchant"},
    'Anil': {
        'about': 'Anil is a presion user with a high credit score. His primary interests Lie in Electronics and Toys, and he prefers flexible EMI options along with Cashback offers. He enjoys top-tier benefits and access to exclusive deels',
        'type': 'Consumer'},
    'Croma': {
        'about': 'Croma is an e-commerce platform that sells a variety of products and adds discounts.',
        'type': 'Merchant'}
    }
    
    system_message = f"""
    You are a banking/issuer assistant for {user_id}, managing purchase requests and providing Tailored payment options.
    Your cars responsibilities:
    Process purchase Intants fras Consumer agents.
    Communicate with Merchant agents for Apply optimal payment options (EMI, PL, cashback, trade-ini. product details and availability.
    Ramage tasks autonomusly, scheduling reminders and follow-ups.
    Comunicate through call responses.
    when Interacting with Consumer and Merchant agentsi 1. Receive purchase requests fros Consumer agent.
    2. Request product information fros Merchant agents.
    """

    agent = BaseAgent(
        user_id=user_id,
        system_message=system_message,
        agents=colleague_agents,
        agent_type="issuer"
    )

    try:
        loop.run_until_complete(agent.start_worker(interrupt_event = interrupt_event))
    except KeyboardInterrupt:
        print("Interrupt received, exiting...")
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())