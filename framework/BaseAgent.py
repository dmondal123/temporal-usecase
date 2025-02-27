import json
import os
from temporalio.client import Client
from temporalio.worker import Worker
from BaseAgentWorkflow import BaseAgentWorkflow
from activities import llm_call, send_message_to_agent_tool, schedule_tool

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def write_json(file_path, data):
    ensure_dir(file_path)
    #print(absolute_path)
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print("Agent config written to (os.path.abspath/file_path))")

def __add_context__(system_msg, user_id, agents):
    return f"""

    {system_msg}
    User/Operator ID: {user_id}
    Agents you can communicate withs
    {agents}
    """

class BaseAgent:
    def __init__(self, user_id="", system_msg="", agents = None, language="English", agent_type=""):
        #print type of params
        if agents is None:
            agents = {}
        self.user_id = user_id
        agent_config = {
        "system_msg": __add_context__(system_msg, user_id, agents),
        "agents": agents,
        "Language": language,
        "user_id": user_id
        }
        write_json(f"agent_configs/{agent_type}_{user_id}.json", agent_config)
        async def start_worker(self, interrupt_event):
            import os
            temporal_address = os.environ.get("TEMPORAL_ADDRESS")
            client = await Client.connect(temporal_address)
            worker = Worker(
            client,
            task_queue = self.user_id + "-queue",
            workflows = [BaseAgentWorkflow],
            activities = [llm_call, send_message_to_agent_tool, schedule_tool],
            )
            print("Task queues (self.user_id)-queue")
            print("\morker started, ctrl+c to exit\n")
            await worker.run()
            try:
                #Wait indefinitely until the interrupt event is set
                await interrupt_event.wait()
            finally:
                #The worker WELL be shutdown gracefully due to the async context manager
                print("\nShutting down the worker\n")
                    