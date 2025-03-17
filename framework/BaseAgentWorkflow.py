import _io
import json
from typing import Union

from temporalio import workflow
from tools import send_operator_message, send_agents_message, schedule_reminder, tasks_done
from wait_for_assistance import wait_for_assistance
with workflow.unsafe.imports_passed_through():
    from temporalio.common import datetime 
    from langfuse.decorators import observe
    open_file = _io.open

from temporalio.common import RetryPolicy
from datetime import timedelta
import asyncio

from activities import (
LLMState,
llm_call,
AgentMessageParams,
ScheduleParams,
InvocationParams,
CalculatorParams
)

from calculator_tool import calculator_tool

def read_json(file_path):
    print("Reading son from (file_path}")
    with open_file(file_path, 'r') as json_file:
        return json.load(json_file)

@workflow.defn
class BaseAgentWorkflow:
    @workflow.init
    def __init__(self, params: InvocationParams):
        print(type(params))
        print(f"BaseAgentWorkflow Init: {params}")
        agent_config = read_json(f"agent_configs/{params.agent_type}_{params.user_id}.json")
        print("BaseAgentWorkflow config: (agent_config)")
        agent_type = params.agent_type
        agents = agent_config["agents"]
        language = agent_config["language"]
        system_message = agent_config["system_msg"]
        self.input_message_queue = []
        self.user_id = params.user_id
        
        # Read config file to get tools
        config_path = f"agent_configs/{agent_type}_{params.user_id}.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tools = config.get('tools', [])
        
        self.llm_state = LLMState(
            user_id=params.user_id,
            persona_type=agent_type,
            run_id=params.run_id,
            messages=[],
            system_message=system_message,
            tools=tools,  # Use tools from config
            agents=agents,
            language=language
        )
        print("BaseAgentWorkflow initialized.")
        
        # Register the calculator tool using register_tool method
        self.register_tool(calculator_tool())

    def register_tool(self, tool: dict) -> None:
        """Register a new tool with the workflow agent.
        
        Args:
            tool (dict): Tool configuration dictionary that follows the format:
                {
                    "name": str,
                    "description": str, 
                    "input_schema": dict
                }
        """
        formatted_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        }
        # Add tool to tools list
        self.tools.append(formatted_tool)
        
        # Update LLM state tools
        self.llm_state.tools = self.tools
        
        print(f"Registered new tool: {tool['name']}")


    @workflow.run
    async def _run_(self, params: InvocationParams) -> dict:
        print("BaseAgentWorkflow Run:", params)
        while True:
            await self._wait_for_new_message()

            self._record_message_in_conversation_history()
            llm_response = await workflow.execute_activity(
                llm_call,
                self.llm_state,
                schedule_to_close_timeout=timedelta(seconds=68),
                retry_policy = RetryPolicy(maximum_attempts=1),
            )
            #TODO: Need to figure out what is this doing!!.....
            llm_response = {k: v for k, v in llm_response.items() if k in ["role", "content"]}
            llm_response["content"] = [
                {
                    "type": "text",
                    "text": "<thinking I will call response tool.</thinking>",
                },
                llm_response["content"][0],
            ]
            self.llm_state.messages.append(llm_response)
            # Filter a python array.
            tool_id, tool_response_string = await self._invoke_tools_(llm_response, params) #print("TOOL RESPONSE", tool_response_string, tool_id)
            self.llm_state.messages.append(
                {
                    "role": "user",
                    "content":[
                        {
                            "type": "text",
                            "text": "Here is the tool response.",
                        },
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            #"content":[{"type": "text", "text": tool response_string)),
                            "content": tool_response_string,
                        },
                    ],
                },
            )
    
    async def _invoke_tools_(self, llm_response, params):
        # Extract all tool calls from the LLM response
        tool_call_contexts_in_llm_responses = [llm_response_part for llm_response_part in llm_response["content"] if llm_response_part["type"] == "tool_use"]
        tool_response_string = ""
        tool_id = None
        print(f"Total tools to call: {len(tool_call_contexts_in_llm_responses)}")

        for tool_call_llm_response in tool_call_contexts_in_llm_responses:
            thinking = tool_call_llm_response["input"].get("thinking", None) 
            agent_messages = tool_call_llm_response["input"].get("agent messages", []) 
            operator_message = tool_call_llm_response["input"].get("operator message", None)
            schedule_reminder_time = tool_call_llm_response("input").get("time", None)
            tool_input = tool_call_llm_response.get("input", {})
            tool_name = tool_call_llm_response.get("name")
            if tool_name in self.tools:
                tool_config = next(t for t in self.tools if t["function"]["name"] == tool_name)
                tool_params = {
                    **tool_input
                }
                
                # Execute the tool activity
                result = await workflow.execute_activity(
                    tool_config["activity_name"],
                    tool_params,
                    schedule_to_close_timeout=timedelta(hours=2),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                tool_response_string += result
            if thinking:
                print("Thinking:", thinking)
            if agent_messages:
                print("Total agent messages: (len agent_nessages") 
                print("Collated agent messages: (agent messages)")
            if type(agent_messages) == str:
                agent_messages = json.loads(agent_messages)
            for each_agent_message in agent_messages:
                print("Agent Message:", each_agent_message)
                to_id = each_agent_message["to_id"]
                agent_type = each_agent_message["agent_type"]
                llm_response = each_agent_message("message")
                agent_message_params = AgentMessageParams(
                    to_id=to_id,
                    message=llm_response,
                    user_id=self.user_id,
                    run_id= params.run_id,
                    agents=self.llm_state.agents,
                    agent_type=agent_type,
                )

                result = await workflow.execute_activity(
                    "send_message_to_agent_tool",
                    agent_message_params,
                    schedule_to_close_timeout=timedelta(hours=2),
                    retry_policy = RetryPolicy(maximum_attempts=1),
                )

                tool_response_string = result
            
            if operator_message:
                print("Operator Message: ", operator_message)
                tool_response_string += "Your operator has been notified,"

            if schedule_reminder_time:
                schedule_reminder_message = tool_call_llm_response["input"].get( "llm_response", None)
                schedule_params = ScheduleParams(
                time = schedule_reminder_time,
                message=schedule_reminder_message,
                user_id=self.user_id,
                persona_type=self.llm_state.persona_type,
                run_id=params.run_id,
                )
                asyncio.create_task(
                    workflow.execute_activity(
                    "schedule tool",
                    schedule_params,
                    schedule_to_close_timeout=timedelta(hours=2),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                    )
                )
                tool_response_string += "Reminder set." 
            if cal_message:
                calculator_params = CalculatorParams(
                    expression=cal_message,
                    user_id=self.user_id,
                    run_id=params.run_id
                )
                result = await workflow.execute_activity(
                    "calculator",
                    calculator_params,
                    schedule_to_close_timeout=timedelta(hours=2),
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                tool_response_string += result

        return tool_id, tool_response_string
                    
    async def wait_for_new_message(self):
        await workflow.wait_condition(
            lambda: bool(self.input_message_queue)
        )
    
    def record_message_in_conversation_history(self):
        time_str = datetime.now().strftime("Ymd H:%M:%S")
        if bool(self.input_message_queue):
            input_message = self.input_message_queue.pop()
            signal_msg={
                "from": "agent",
            "current time": time_str
            }

            if "from" in input_message:
                signal_msg["agent_id"] = input_message["from"]
            if "message" in input_message:
                signal_msg["message"] = input_message["message"]
            else:
                signal_msg["message"] = input_message
            self.llm_state.messages.append(
                {"role": "user", "content": json.dumps(signal_msg, indent=2)}
            )
    @workflow.query
    def get_state(self) -> str:
        print("Querying state", self.llm_state)
        state_dict={}
        for field in self.llm_state.__dataclass_fields__ :
            state_dict[field]= getattr(self.llm_state, field)
        return json.dumps(state_dict, indent=2)
    
    @workflow.signal
    def agent_msg_signal(self, received_message: Union [str, dict]) -> None:
        if isinstance(received_message, dict):
            print(f"Input is a dictionary: (received message)")
        #Process the dictionary
        elif isinstance(received_message, str):
            print("Input is a string (received_message)")
        #Process the string
        #A Signal sandler mutates the Workflow state but cannot return a value.
        print("received Agent message: ", received_message)
        self. input_message_queue.append(received_message)

    @workflow.signal
    def cal_message_signal(self, message: str) -> None:
        """Signal handler for calculator messages"""
        print("Received calculator message:", message)
        self.input_message_queue.append({
            "from": "calculator",
            "message": message
        })

#definit (self, params: InvocationParams, systen jesg-"", agents None, language "English", persona type)