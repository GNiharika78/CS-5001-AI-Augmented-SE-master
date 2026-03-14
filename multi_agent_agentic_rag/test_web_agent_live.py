from dotenv import load_dotenv
from src.agents.web_agent import WebAgent

load_dotenv()

agent = WebAgent()
result = agent.run("latest renewable energy policy updates in Europe")

print("Agent:", result.agent_name)
print("Summary:", result.summary)
for source in result.sources:
    print(source.title)
    print(source.metadata)
    print(source.snippet)
    print("-" * 80)