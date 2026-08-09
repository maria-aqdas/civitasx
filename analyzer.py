import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_policy(policy_text):
    prompt = f"""
    You are a helpful Public Policy Analyst who explains things in very simple, everyday English.

    Analyze the following public policy proposal for its societal, economic, and environmental impacts.

    Policy Proposal:
    {policy_text}

    IMPORTANT WRITING RULES (follow these strictly):
    - Use SIMPLE, EASY English. Write like you are explaining it to a normal person who is not a lawyer or expert.
    - Avoid difficult words, legal jargon, and long complicated sentences.
    - Use short sentences (max 15-18 words each).
    - Every bullet point in benefits, risks, and environmental_impact must be ONE short, clear sentence a regular person can understand in one read.

    Provide your response STRICTLY in valid JSON format with this exact structure:
    {{
      "policy_title": "A short, clean title for this policy",
      "summary": "A simple 2-3 sentence summary in easy English, explaining what the policy does.",
      "benefits": [
        "First major benefit, in one simple sentence",
        "Second major benefit, in one simple sentence"
      ],
      "risks": [
        "First major risk or drawback, in one simple sentence",
        "Second major risk, in one simple sentence"
      ],
      "environmental_impact": [
        "Effect on environment or society, in one simple sentence",
        "Second environmental/societal effect, in one simple sentence"
      ],
      "scores": {{
        "economic_impact": 75,
        "social_equity": 60,
        "environmental_benefit": 85,
        "public_sentiment": 50
      }}
    }}
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    return json.loads(response.text)