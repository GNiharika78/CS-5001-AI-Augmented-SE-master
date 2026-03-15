Multi-Agent agentic RAG system

Overview:
This projects implements a Muilti-Agent agentic Retrieval Augmented Generation(RAG) System, that answers complex questions by coordinating multiple specialized agents. Instead of reklying on single retrieval pipeline, the system distributes tasks across multiple agents for different data sources and retrieval strategies.

The system inspired by Multi-agent agentic RAG architecture, where coordinator agent orchestrates specialized retrieval agents, integrates their outputs and generates a response using LLM.

This approach improves modularity, scalability and retrieval quality and allows the system to combine strcutural data, academic knowledge and live web information.

System architecture:

It follows multi-agent workflow.

User Query
     │
     ▼
Planner Agent
(decides which agents are needed)
     │
     ▼
Coordinator Agent
(orchestrates execution)
     │
     ├── SQL Agent (structured data)
     ├── Paper Retrieval Agent (academic knowledge)
     ├── Web Agent (live web search)
     └── Recommendation Agent (suggests further reading)
     │
     ▼
Synthesizer Agent (LLM)
     │
     ▼
Final Answer


Agents in the system:

Coordinator agent:
This acts as a central orchestrator of the system . It receives the user query and calls the planner agents to determine which agents are needed, executes the selected agents and passes their outputs to the synthesizer agent.

Responsibilities: Route queries, execute agents, collect results, track latency and cost and produce final response.

Planner Agent:
 It analyzes the user query and determines which agent should run.

 Query Type                    Selected agents
statistical comparision        SQL agent
research/academic analysis     Paper agent
currrent events or policies    web agent
reading suggestions            recommendation agent


Sql agent:
It retrieves the structured data from database.

Data sources include: renewable energy share, emission data, investment statistics, employment indicators

these are stored in a SQLite database built from csv datasets.

Example questions handled by it:
1. compare renewable share across countries
2. emissions statistics
3. energy investment comparisions

paper retrieval agent:

It performs semantic retrieval across academic documents and reports.
Sources included: energy transition research papers, policy analysis reports, expert commentary.

Documents are embedded into vector database to enable semantic search.

example questions handled:
academic insights on energy transitions, policy design impacts, research summaries
