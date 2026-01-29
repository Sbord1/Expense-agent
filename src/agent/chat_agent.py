from typing import List, Dict
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """
You are a personal finance assistant.

You are given structured insights about the user's spending.
Your job is to:
- explain them clearly
- give practical advice
- NEVER invent data
- NEVER assume facts not present in the insights
- be concise and actionable
"""


def chat_about_insights(
    user_message: str,
    insights: List[Dict]
) -> str:
    """
    LLM interprets insights only.
    No DB access.
    No calculations.
    """

    insights_json = json.dumps(insights, indent=2)

    prompt = f"""
User question:
{user_message}

Available insights:
{insights_json}

Explain the situation and give advice.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content