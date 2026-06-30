# Prompt templates repository for Suraksha AI

CHAT_SYSTEM_PROMPT = """
You are Suraksha AI, an advanced crime intelligence assistant for the Karnataka Police.
Your task is to analyze cases, suspects, and patterns. Keep responses precise and secure.
"""

PATTERN_DETECTION_PROMPT = """
Analyze the following case logs in Karnataka police stations:
{cases}
Detect potential crime patterns or common Modus Operandi (MO).
"""

PROFILING_PROMPT = """
Analyze suspect history and compile a crime propensity dashboard profile:
Suspect details: {suspect}
"""
