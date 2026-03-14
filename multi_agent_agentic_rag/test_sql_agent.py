from src.agents.sql_agent import SQLAgent

agent = SQLAgent()
query = "What are the economic and environmental impacts of renewable energy adoption in Europe?"
result = agent.run(query)

print("Agent:", result.agent_name)
print("Summary:", result.summary)
print("Latency:", result.latency_ms)
print("Cost:", result.cost_usd)
print("\nSources:\n")

for source in result.sources:
    print(source.title)
    print(source.snippet)
    print(source.metadata)
    print("-" * 80)