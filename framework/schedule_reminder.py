def schedule_reminder():
    return '''{
  "name": "schedule_reminder",
  "description": "Schedule yourself reminders tp follow up on tasks or messages. The reminder will be sent to you at the specified time.",
  "input_schema": {
    "properties": {
      "thinking": {
        "description": "The 'thinking' parameter is a string that represents the thought process or reasoning behind a decision or action. It should be used to provide context or explanation for the function's output or behavior.",
        "title": "Thinking",
        "type": "string"
      },
      "time": {
        "description": "The 'time' parameter is an integer representing a duration or timestamp, typically measured in seconds or milliseconds. It should be used to specify a time interval or a specific point in time for the function's operation.",
        "title": "Time",
        "type": "integer"
      },
      "message": {
        "description": "The 'message' parameter is a string that represents the content or data to be processed or displayed by the function. It should be passed as a valid string value.",
        "title": "Message",
        "type": "string"
      }
    },
    "required": [
      "thinking",
      "time",
      "message"
    ],
    "title": "schedule_reminderInput",
    "type": "object"
  }
}'''
