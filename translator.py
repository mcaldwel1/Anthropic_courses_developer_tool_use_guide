import anthropic 
import wikipedia 
import getpass 
import os 
import json

client = anthropic.Anthropic(
    api_key = getpass.getpass("Enter your anthropic API key: ")
)

translator_tool = {
    "name": "translator",
    "description": "translates a phrase from a given language to English, Spanish, French, Japanese, and Arabic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "English": {
                "type": "string",
                "description": "the given phrase to be translated"
            },
            "Spanish": {
                "type": "string",
                "description": "the phrase in Spanish"
            },
            "French": {
                "type": "string",
                "description": "the phrase in French"
            },
            "Japanese": {
                "type": "string",
                "description": "the phrase in Japanese"
            },
            "Arabic": {
                "type": "string",
                "description": "the phrase in Arabic"
            }
        },
        "required": ["English", "Spanish", "French", "Japanese", "Arabic"],
    }
}

def translate_phrase(phrase):
    prompt = f"Translate {phrase} to English, Spanish, French, Japanese, and Arabic. Use the translator tool in your response."
    messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model = "claude-3-5-haiku-20241022",
        messages = messages,
        tools = [translator_tool],
        max_tokens = 600
    )
    translations_from_claude = None

    if(response.stop_reason == 'tool_use'):
        tool_use = response.content[-1]
        tool_name = tool_use.name
        tool_input = tool_use.input

        if(tool_name == 'translator'):
            translations_from_claude = tool_use.input
    
    print(json.dumps(translations_from_claude, ensure_ascii=False, indent=2))

translate_phrase('Captain, watch out!')