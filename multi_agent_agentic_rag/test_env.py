from dotenv import load_dotenv
import os

load_dotenv()

print("OPENAI_API_KEY exists:", bool(os.getenv("OPENAI_API_KEY")))
print("TAVILY_API_KEY exists:", bool(os.getenv("TAVILY_API_KEY")))
print("TAVILY prefix:", (os.getenv("TAVILY_API_KEY") or "")[:8])