import json
import os
from temporalio.client import Client
from temporalio.worker import Worker
from BaseAgentWorkflow import BaseAgentWorkflow
from activities import llm_call, send_message_to_agent_tool, schedule_tool, calculator

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def write_json(file_path, data):
    ensure_dir(file_path)
    # Convert any non-serializable objects to strings first
    def serialize(obj):
        try:
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)
            
    # Recursively handle nested dictionaries and lists
    def clean_data(d):
        if isinstance(d, dict):
            return {k: clean_data(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_data(v) for v in d]
        else:
            return serialize(d)
    
    cleaned_data = clean_data(data)
    
    with open(file_path, 'w') as json_file:
        json.dump(cleaned_data, json_file, indent=4)
    print(f"Agent config written to {os.path.abspath(file_path)}")

def __add_context__(system_msg, user_id, agents):
    return f"""
    {system_msg}
    User/Operator ID: {user_id}
    Agents you can communicate with:
    {agents}
    """

class BaseAgent:
    def __init__(self, user_id="", system_msg="", agents=None, language="English", agent_type=""):
        if agents is None:
            agents = {}
        self.user_id = user_id
        self.agent_type = agent_type
        self.activities = [llm_call, send_message_to_agent_tool, schedule_tool, calculator]
        self.additional_tools = []  # Initialize empty list for additional tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "send_message_to_agent",
                    "description": "Send a message to another agent",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["agent_id", "message"]
                    }
                }
            }
        ]  # Initialize with default tools
        
        agent_config = {
            "system_msg": __add_context__(system_msg, user_id, agents),
            "agents": agents,
            "Language": language,
            "user_id": user_id,
            "tools": self.tools,  # Add tools to config
            "additional_tools": self.additional_tools
        }
        self.config_path = f"agent_configs/{agent_type}_{user_id}.json"
        write_json(self.config_path, agent_config)

    def register_tool(self, tool: dict) -> None:
        """Register a tool configuration for the LLM to use.
        
        Args:
            tool (dict): Tool configuration with name, description, and parameters
        """
        self.additional_tools.append(tool)
        # Read current config
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Update tools
        if 'tools' not in config:
            config['tools'] = []
        config['tools'].append(tool)
        
        # Write updated config
        write_json(self.config_path, config)
        print(f"Registered new tool: {tool['name']}")

    async def start_worker(self, interrupt_event):
        import os
        temporal_address = os.environ.get("TEMPORAL_ADDRESS")
        client = await Client.connect(temporal_address)
        worker = Worker(
            client,
            task_queue=self.user_id + "-queue",
            workflows=[BaseAgentWorkflow],
            activities=[llm_call, send_message_to_agent_tool, schedule_tool, calculator, register_tool_activity],
        )
        print(f"Task queue: {self.user_id}-queue")
        print("\nWorker started, ctrl+c to exit\n")
        await worker.run()
        try:
            await interrupt_event.wait()
        finally:
            print("\nShutting down the worker\n")
                    