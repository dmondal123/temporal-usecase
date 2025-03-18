import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# While we could use multiple parameters in the activity, Temporal strongly
# encourages using a single dataclass instead which can have fields added to it
# in a backwards-compatible way.
@dataclass
class ComposeGreetingInput:
    greeting: str
    name: str


@dataclass
class CalculatorInput:
    operation: str  # "add", "subtract", "multiply", "divide"
    x: float
    y: float


# Basic activity that logs and does string concatenation
@activity.defn
async def compose_greeting(input: ComposeGreetingInput) -> str:
    activity.logger.info("Running activity with parameter %s" % input)
    return f"{input.greeting}, {input.name}!"


@activity.defn
async def calculate(input: CalculatorInput) -> float:
    activity.logger.info("Running calculator activity with parameter %s" % input)
    match input.operation:
        case "add":
            return input.x + input.y
        case "subtract":
            return input.x - input.y
        case "multiply":
            return input.x * input.y
        case "divide":
            if input.y == 0:
                raise ValueError("Division by zero")
            return input.x / input.y
        case _:
            raise ValueError(f"Unknown operation: {input.operation}")


# Basic workflow that logs and invokes an activity
@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info("Running workflow with parameter %s" % name)
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            start_to_close_timeout=timedelta(seconds=10),
        )


@workflow.defn
class CalculatorWorkflow:
    @workflow.run
    async def run(self, operation: str, x: float, y: float) -> float:
        workflow.logger.info(f"Running calculator workflow with operation {operation}, x={x}, y={y}")
        return await workflow.execute_activity(
            calculate,
            CalculatorInput(operation, x, y),
            start_to_close_timeout=timedelta(seconds=10),
        )


@workflow.defn
class CombinedWorkflow:
    @workflow.run
    async def run(self, operation: str, x: float, y: float, name: str) -> dict:
        workflow.logger.info(f"Running combined workflow with operation {operation}, x={x}, y={y}, name={name}")
        
        # Execute calculator activity
        calc_result = await workflow.execute_activity(
            calculate,
            CalculatorInput(operation, x, y),
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        # Execute greeting activity
        greeting_result = await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput("Hello", name),
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        return {
            "calculation": calc_result,
            "greeting": greeting_result
        }


async def main():
    # Uncomment the lines below to see logging output
    # import logging
    # logging.basicConfig(level=logging.INFO)

    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="hello-activity-task-queue",
        workflows=[CombinedWorkflow],  # Replace previous workflows with combined one
        activities=[compose_greeting, calculate],
    ):

        # While the worker is running, use the client to run the workflow and
        # print out its result. Note, in many production setups, the client
        # would be in a completely separate process from the worker.
        result = await client.execute_workflow(
            CombinedWorkflow.run,
            args=["add", 5, 3, "World"],
            id="combined-workflow-id",
            task_queue="hello-activity-task-queue",
        )
        print(f"Combined Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())