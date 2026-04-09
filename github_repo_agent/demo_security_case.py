# Demo file for agent review (do not use real secrets)
import os

TOKEN = os.getenv("DEMO_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing DEMO_TOKEN environment variable")