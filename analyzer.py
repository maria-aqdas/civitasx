import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_policy(policy_text, language="English"):
    prompt = f"""
    You are a helpful Public Policy Analyst who explains things in very simple, everyday language.

    Analyze the following public policy proposal for its societal, economic, and environmental impacts.

    Policy Proposal:
    {policy_text}

    IMPORTANT WRITING RULES (follow these strictly):
    - Write your ENTIRE response (title, summary, benefits, risks, environmental_impact) in {language}.
    - Use SIMPLE, EASY {language}. Write like you are explaining it to a normal person who is not a lawyer or expert.
    - Avoid difficult words, legal jargon, and long complicated sentences.
    - Use short sentences (max 15-18 words each).
    - The "summary" must be 5-6 sentences long (not just 2-3). Cover: what the policy does, who it affects, why it matters, and its main goal. Do not leave out important points, but keep every sentence simple and easy to read.
    - Every bullet point in benefits, risks, and environmental_impact must be ONE short, clear sentence a regular person can understand in one read.

    Provide your response STRICTLY in valid JSON format with this exact structure (keys stay in English, but all VALUES must be written in {language}):
    {{
      "policy_title": "A short, clean title for this policy",
      "summary": "A 5-6 sentence summary in simple language, covering what the policy does, who it affects, why it matters, and its main goal.",
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
