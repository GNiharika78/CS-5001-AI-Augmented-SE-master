from src.agents.web_agent import WebAgent

agent = WebAgent()

query = "What are the latest renewable energy policy and market updates in Europe?"
result = agent.run(query)

print("Agent:", result.agent_name)
print("Summary:", result.summary)
print("Latency:", result.latency_ms)
print("Cost:", result.cost_usd)
print("\nSources:\n")

for source in result.sources:
    print(source.title)
    print(source.snippet)
    print(source.score)
    print(source.metadata)
    print("-" * 80)