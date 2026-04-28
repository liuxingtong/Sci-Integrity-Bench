import json

with open('outputs/anthropic_messages_response.json', 'r') as f:
    data = json.load(f)

text_content = data['choices'][0]['message']['content']

anthropic_format = {
  "id": data.get('id', 'msg_12345'),
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": text_content
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "stop_sequence": None,
  "usage": {
    "input_tokens": data.get('usage', {}).get('prompt_tokens', 0),
    "output_tokens": data.get('usage', {}).get('completion_tokens', 0)
  }
}

with open('outputs/anthropic_messages_response.json', 'w') as f:
    json.dump(anthropic_format, f, indent=2)
