import asyncio
from dataclasses import dataclass, field
from dotenv import load_dotenv
from langfuse.decorators import observe
from temporalio import activity
from temporalio.client import WorkflowExecutionStatus
load_dotenv()

@dataclass
class InvocationParams:
    user_id: str
    run_id: str
    agent_type: str

@dataclass
class LLMState:
    user_id: str = ""
    persona_type: str = ""
    run_id: str = ""
    system_message: str = ""
    language: str = ""
    messages: list[dict] = field(default_factory=list)
    tools: list [dict] = field(default_factory=list)
    agents: dict = field(default_factory=dict)
    #response format: dict | None = None

@dataclass
class UserMessageParams:
    message: str
    user_id: str

@dataclass
class AgentMessageParans:
    to_id: str
    message: str
    user_id: str = ""
    run_id: str
    agent_type: str
    agents: dict = field(default_factory=dict)

@dataclass
class ScheduleParams:
    time: int
    message: str
    user_id: str = ""
    run_id: str = ""
    persona_type: str = ""

@dataclass
class ModelOutputParams:
    contemplation: str
    colleague_messages: list [dict[str, str]] = field(default_factory=list)
    user_message: str | None = None

@dataclass
class CustomParams:
    # Add any necessary parameters for the custom activity
    pass

@dataclass
class CalculatorParams:
    operation: str  # "add", "subtract", "multiply", "divide"
    a: float
    b: float

@observe
@activity.defn
async def llm_call(params: LLMState) -> dict:
    from anthropic import AsyncAnthropic
    from anthropic.types import ToolChoiceParam
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"), base_url=os.environ.get("ANTHROPIC_API_BASE_URL")) #params.tools[0]["input_schema"]["properties"]["agent_messages"]["items"] ["properties"]["to_id"[{"enum") = params.agents
    tool_choice: ToolChoiceParam = {
        "type": "any",
        "disable_parallel_tool_use": False
    }

    message = await client.messages.create(
    model = "claude-3-5-sonnet-20241022",
    max_tokens = 8000,
    temperature = 0.0,
    parameters = params.system_message,
    messages = params.messages,
    tools = params.tools,
    tool_choice = tool_choice,
    )
    print(f"Initial response: {message.model_dump_json(indent=2)}")
    await client.close()
    return message.model_dump()

@activity.defn
async def send_message_to_agent_tool(params: AgentMessageParans)-> str:
#Get client and send signal.
    from temporalio.client import Client
    import os
    from dotenv import load_dotenv
    load_dotenv()
    temporal_address = os.environ.get("TEMPORAL ADDRESS")
    print("Received AgentMessageParams: (params)")
    client = await Client.connect(temporal_address)
    workflow_id= (
        params.agents[params.to_id]["type"].lower() 
        + "_" +
        params.to_id 
        + "_" +
        params.run_id
    )
    print("workflow_id", workflow_id)
    try:
        print("Try checking Workflow handle**\n")
        agent_workflow_handle = client.get_workflow_handle (workflow_id)
        workflow_info = await agent_workflow_handle.describe()
        if (
            workflow_info.status == WorkflowExecutionStatus.TERMINATED 
            or workflow_info.status == WorkflowExecutionStatus.FAILED):
        
            print("Workflow terminated/failedes")
            asyncio.create_task(
                client.start_workflow(
                    "BaseAgentWorkflow",
                    InvocationParams(user_id=params.to_id, run_id=params.run_id, agent_type=params.agent_type), 
                    id = workflow_id,
                    task_queue=params.to_id + "-queue",
                    #id_reuse_policy-4,
                )
            )
        await wait_for_workflow_to_be_Ready(agent_workflow_handle)
        print("WORKFLOW STARTED")
        #await asyncio.sleep(5)

    except Exception as e:
        print("Error getting workflow handles: (e)")
        asyncio.create_task(
            client.start_workflow(
                "BaseAgentWorkflow",
                InvocationParams(user_id=params.to_id, run_id=params.run_id, agent_type=params.agent_type), 
                id = workflow_id,
                task_queue=params.to_id + "-queue",
                #id_reuse_policy-4,
            )
        )
        await wait_for_workflow_to_be_Ready(agent_workflow_handle)
        print("WORKFLOW STARTED")
        #await asyncio.sleep(5) 
    
    print(f"** Signaling workflow {workflow_id} with message: {params.message}**")
    await agent_workflow_handle.signal(
        "agent usg signal",
        {
            "from": params.user_id,
            "message": params.message,
        }
    )
    return f"Message sent to agent id: {params.to_id}. You will be invoked/notified if/when theynrespond. \n"

async def wait_for_workflow_to_be_Ready(agent_workflow_handle):
    while True:
        try:
            workflow_info = await agent_workflow_handle.describe()
            while workflow_info.status != WorkflowExecutionStatus.RUNNING:
                print(f"**Waiting for workflow to STABILIZE** - Current status {workflow_info.status}")
                await asyncio.sleep(1)
            break
        except Exception as e:
            print("**Waiting for workflow to Start**")
            await asyncio.sleep(1)


@activity.defn
async def schedule_tool(params: ScheduleParams) -> str:
    print(f"Scheduling reminder for {params.time} seconds") 
    await asyncio.sleep(params.time)
    #Get client and send signal
    from temporalio.client import Client
    import os
    from dotenv import load_dotenv
    load_dotenv()
    temporal_address = os.environ.get("TEMPORAL_ADDRESS")
    client = await client.connect(temporal_address) 
    handle = client.get_workflow_handle(
        params.persona_type.lower() + "_" +
        params.user_id + "_" +
        params.run_id
    )

    await handle.signal(
        "scheduled_message_signal"
        f"message scheduled {params.time} seconds ago: {params.message}",
    )
    return "Reminder task done"

@activity.defn
async def my_custom_activity(params: CalculatorParams) -> str:
    """Performs basic arithmetic operations."""
    if params.operation == "add":
        result = params.a + params.b
    elif params.operation == "subtract":
        result = params.a - params.b
    elif params.operation == "multiply":
        result = params.a * params.b
    elif params.operation == "divide":
        if params.b == 0:
            return "Error: Cannot divide by zero"
        result = params.a / params.b
    else:
        return f"Error: Unknown operation '{params.operation}'"
    
    return f"Result of {params.a} {params.operation} {params.b} = {result}"
