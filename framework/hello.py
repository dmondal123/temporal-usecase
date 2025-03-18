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
class CombinedWorkflow:
    @workflow.run
    async def run(self, operation: str, x: float, y: float, name: str, should_greet: bool) -> dict:
        workflow.logger.info(f"Running combined workflow with operation {operation}, x={x}, y={y}, name={name}")
        
        # Execute calculator activity
        calc_result = await workflow.execute_activity(
            calculate,
            CalculatorInput(operation, x, y),
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        result = {"calculation": calc_result}
        
        # Only execute greeting if should_greet is True
        if should_greet:
            greeting_result = await workflow.execute_activity(
                compose_greeting,
                ComposeGreetingInput("Hello", name),
                start_to_close_timeout=timedelta(seconds=10),
            )
            result["greeting"] = greeting_result
        
        return result


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

        while True:
            print("\nCalculator Operations: add, subtract, multiply, divide")
            print("Type 'exit' to quit")
            
            operation = input("Enter operation: ").lower()
            if operation == 'exit':
                break
            
            if operation not in ["add", "subtract", "multiply", "divide"]:
                print("Invalid operation!")
                continue
            
            try:
                x = float(input("Enter first number: "))
                y = float(input("Enter second number: "))
            except ValueError:
                print("Please enter valid numbers!")
                continue
            
            name = input("Enter your name (or press Enter to skip greeting): ")
            should_greet = bool(name and name.lower() == "hello")
            
            result = await client.execute_workflow(
                CombinedWorkflow.run,
                args=[operation, x, y, name, should_greet],
                id=f"combined-workflow-id-{operation}-{x}-{y}",
                task_queue="hello-activity-task-queue",
            )
            print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())