def calculator():
    return '''{
  "name": "calculator",
  "description": "A calculator tool for performing basic arithmetic operations.",
  "parameters": {
    "type": "object",
    "properties": {
      "params": {
        "type": "string",
        "description": "CalculatorParams is an object containing input values required for performing calculations in a calculator application."
      }
    },
    "required": [
      "params"
    ]
  }
}'''
