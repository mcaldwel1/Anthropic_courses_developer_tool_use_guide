import anthropic
import getpass
import os
import wikipedia

client = anthropic.Anthropic(
    api_key = getpass.getpass("Enter your anthropic API key: ")
)

def generate_wikipedia_reading_list(research_topic, article_titles):
    wikipedia_articles = []
    for t in article_titles:
        results = wikipedia.search(t)
        try:
            page = wikipedia.page(results[0])
            title = page.title
            url = page.url
            wikipedia_articles.append({"title": title, "url": url})
        except:
            continue
    add_to_research_reading_file(wikipedia_articles, research_topic)

generate_wiki_list_tool = {
    "name": "generate_wiki_list",
    "description": "accepts a list of articles and parses the list for valid Wikipedia articles",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "the research topic"
            },
            "articles": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "a list of generated articles"
            }
        },
        "required": ["topic", "articles"]
    }
}

def add_to_research_reading_file(articles, topic):
    with open("./research_reading.md", "a", encoding="utf-8") as file:
        file.write(f"## {topic} \n")
        for article in articles:
            title = article["title"]
            url = article["url"]
            file.write(f"* [{title}]({url}) \n")
        file.write(f"\n\n")

def get_research_help(subject, number):

    prompt = f"Give me a list of {number} real Wikipedia article titles to read about {subject}."
    
    messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model = "claude-3-haiku-20240307",
        messages = messages,
        max_tokens = 500,
        tools = [generate_wiki_list_tool],
    )

    if(response.stop_reason == "tool_use"):
        tool_use = response.content[-1]
        tool_name = tool_use.name
        tool_input = tool_use.input

        if(tool_name == "generate_wiki_list"):
            topic = tool_input["topic"]
            articles = tool_input["articles"]
            generate_wikipedia_reading_list(topic, articles)

get_research_help("actors of the 20th century", 7)