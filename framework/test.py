from openai import OpenAI
from dataclasses import dataclass

@dataclass
class CalculatorParams:
    expression: str

import re
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-3.5-turbo"
def calculator(params: CalculatorParams):
    import re
    # Remove any non-digit or non-operator characters from the expression   
    try:
        params.expression = re.sub(r'[^0-9+\-*/().]', '', params.expression)
        # Evaluate the expression using the built-in eval() function
        result = eval(params.expression)
        return f"Output of {params.expression} is {result}"
    except (SyntaxError, ZeroDivisionError, NameError, TypeError, OverflowError):
        return "Error: Invalid expression"
    
calculator_tool = [{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform basic arithmetic calculations",
        "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
        }
    }
}]

def make_query_and_print_result(messages, tools=None):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=1000,
        tools=tools or [calculator_tool],
        tool_choice="auto"
    )

    for choice in response.choices:
        message = choice.message
        if message.content:
            print(message.content)
        if message.tool_calls:
            for tool_call in message.tool_calls:
                print(f"Tool: {tool_call.function.name}({tool_call.function.arguments})")

    return response

def add_messages(messages, role, content):
    if isinstance(content, str):
        messages.append({"role": role, "content": content})
    elif hasattr(content, 'tool_calls') and content.tool_calls:
        # For tool calls from OpenAI response
        messages.append({
            "role": role,
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in content.tool_calls
            ]
        })
    else:
        # Default to content as string if no tool calls
        messages.append({"role": role, "content": str(content)})

MESSAGES = [
    {"role": "user", "content": "What's 2 + 4?"}
]

response = make_query_and_print_result(MESSAGES)

# Handle the response properly based on whether it's a tool call or regular message
if response.choices[0].message.tool_calls:
    add_messages(MESSAGES, "assistant", response.choices[0].message)
else:
    add_messages(MESSAGES, "assistant", response.choices[0].message.content)

add_messages(MESSAGES, "user", "Tell me the answer")
response = make_query_and_print_result(MESSAGES)

if response.choices[0].message.tool_calls:
    add_messages(MESSAGES, "assistant", response.choices[0].message)
else:
    add_messages(MESSAGES, "assistant", response.choices[0].message.content)