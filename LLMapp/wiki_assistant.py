from dotenv import load_dotenv
from anthropic import Anthropic
import wikipedia
import getpass
import os
import json

load_dotenv()

client = Anthropic(
    api_key = getpass.getpass("Enter your Anthropic API Key:")
)
    
def get_info(research_topic):
    results = wikipedia.search(research_topic)
    result = results[0]
    wiki_page = wikipedia.page(result, auto_suggest=False)
    return wiki_page.content

get_info_tool = {
    "name": "info_getter",
    "description": "A tool to retrieve an up to date Wikipedia article",
    "input_schema": {
        "type": "object",
        "properties": {
            "research_topic": {
                "type": "string",
                "description": "The search term to find a wikipedia article by title"
            }
        },
        "required": ["research_topic"]
    }
}

def prompt_claude(prompt): 
    messages = [{"role": "user", "content": prompt}]

    system_prompt = """
    You will be asked a question by the user. 
    If answering the question requires data you were not trained on, you can use the get_article tool to get the contents of a recent wikipedia article about the topic. 
    If you can answer a question without needing to call the tool, please answer without calling any tools.
    Only call the tool when needed. 
    """
    while(True):
        if(messages[-1].get("role") == "assistant"):
            user_message = input("\nEnter Another Question: ")
            messages.append({"role": "user", "content": user_message})
        try:
            response = client.messages.create(
                model = "claude-3-haiku-20240307",
                system = system_prompt,
                messages = messages,
                max_tokens = 500,
                tools = [get_info_tool]
            )

            if(response.content[0].type == "tool_use"):
                tool_use = response.content[-1]
                tool_name = tool_use.name
                tool_input = tool_use.input

                messages.append({"role": "assistant", "content": response.content})
                
                if(tool_name == "info_getter"):
                    search_term = tool_input["research_topic"]
                    wiki_result = ''
                    wiki_result += get_info(search_term)
                    tool_response = {
                        "role": "user",
                        "content": [
                            {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": wiki_result
                            }
                        ]
                    }
                    messages.append(tool_response)

                    response = client.messages.create(
                        model = "claude-3-haiku-20240307",
                        messages = messages,
                        max_tokens = 350,
                        tools = [get_info_tool]
                    )
            else:
                messages.append({"role": "assistant", "content": response.content})
                print(response.content[0].text)
        except: 
            print('program exited')
            break

user_input = input("User: ")
prompt_claude(user_input)
