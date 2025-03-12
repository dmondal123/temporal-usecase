from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "o3-mini"
def calculator(operation, num1, num2):
    try:
        num1 = float(num1)
        num2 = float(num2)
        if operation == "add":
            return num1 + num2
        elif operation == "subtract":
            return num1 - num2
        elif operation == "multiply":
            return num1 * num2
        elif operation == "divide":
            return num1 / num2 if num2 != 0 else "Error: Division by zero"
        else:
            return "Error: Invalid operation"
    except ValueError:
        return "Error: Invalid numbers"
    
calculator_tool = [
    {
        "name": "calculator",
        "description": "Perform basic arithmetic operations",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform"
                },
                "num1": {
                    "type": "number",
                    "description": "The first number"
                },
                "num2": {
                    "type": "number",
                    "description": "The second number"
                },
            },
            "required": ["operation", "num1", "num2"]
        }
    }
]

file_tool = [
    {
        "name": "save_file",
        "description": "Save content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path where the file should be saved"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["filepath", "content"]
        }
    }
]

def save_file(filepath, content):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write the content to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved file to {filepath}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

def make_query_and_print_result(messages, tools=None):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        functions=file_tool,
        function_call={"name": "save_file"},
        reasoning_effort="low"
    )

    for choice in response.choices:
        message = choice.message
        if message.content:
            print(message.content)
        if message.function_call:
            print(f"Tool: {message.function_call.name}({message.function_call.arguments})")

    return response

def add_messages(messages, role, content):
    if isinstance(content, str):
        messages.append({"role": role, "content": content})

MESSAGES = [
    {"role": "system", "content": "You must break down complex calculations into steps using the calculator tool. The calculator can only handle two numbers at a time with basic operations (add, subtract, multiply, divide). Show your work step by step using the calculator tool."},
    {"role": "user", "content": "What's (50+6*3)* (72 / 8) / (15 - 3 * 2)? Break this down step by step using the calculator tool."}
]

response = make_query_and_print_result(MESSAGES)

if response.choices[0].message.content:
    add_messages(MESSAGES, "assistant", response.choices[0].message.content)