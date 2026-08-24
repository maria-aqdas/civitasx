import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
 
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _get_depth_instructions(word_count):
    """Decide how long the summary and how many bullet points to ask for,
    based on how long the input policy document is."""
    if word_count < 150:
        return {
            "summary_len": "3-4 sentences",
            "bullet_count": "2-3",
        }
    elif word_count < 600:
        return {
            "summary_len": "5-7 sentences",
            "bullet_count": "3-4",
        }
    else:
        return {
            "summary_len": "8-10 sentences (a full, thorough paragraph)",
            "bullet_count": "5-6",
        }


def analyze_policy(policy_text, language="English"):
    # Cap document length so we stay safely under the Gemini free-tier
    # per-minute input token limit. Roughly 1 word ≈ 1.3 tokens, so
    # ~12,000 words keeps a single request comfortably under 250k tokens
    # even with the rest of the prompt included.
    MAX_WORDS = 12000
    words = policy_text.split()
    was_truncated = len(words) > MAX_WORDS
    if was_truncated:
        policy_text = " ".join(words[:MAX_WORDS])

    word_count = len(policy_text.split())
    depth = _get_depth_instructions(word_count)

    truncation_note = (
        f"\n\nNOTE: This document was very long, so only the first "
        f"{MAX_WORDS} words are shown above. Base your analysis on this portion."
        if was_truncated else ""
    )

    prompt = f"""
    You are a helpful Public Policy Analyst who explains things in very simple, everyday language.

    Analyze the following public policy proposal for its societal, economic, and environmental impacts.

    Policy Proposal (approximately {word_count} words):
    {policy_text}{truncation_note}

    IMPORTANT WRITING RULES (follow these strictly):
    - Write your ENTIRE response (title, summary, benefits, risks, environmental_impact) in {language}.
    - Use SIMPLE, EASY {language}. Write like you are explaining it to a normal person who is not a lawyer or expert.
    - Avoid difficult words, legal jargon, and long complicated sentences.
    - Use short sentences (max 15-18 words each).
    - The length of your answer must match the length and detail of the source document:
        - The "summary" must be {depth['summary_len']} long. Cover what the policy does, who it affects, why it matters, and its main goal. Do not skip important details found in the document.
        - Provide {depth['bullet_count']} bullet points EACH for "benefits", "risks", and "environmental_impact". If the document does not contain enough distinct points for the higher end of that range, provide as many genuinely distinct, meaningful points as the document supports — never invent filler points just to hit a number.
    - Every bullet point in benefits, risks, and environmental_impact must be ONE short, clear sentence a regular person can understand in one read.

    Provide your response STRICTLY in valid JSON format with this exact structure (keys stay in English, but all VALUES must be written in {language}):
    {{
      "policy_title": "A short, clean title for this policy",
      "summary": "A summary in simple language, following the length rule above.",
      "benefits": [
        "First major benefit, in one simple sentence"
      ],
      "risks": [
        "First major risk or drawback, in one simple sentence"
      ],
      "environmental_impact": [
        "Effect on environment or society, in one simple sentence"
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

    result = json.loads(response.text)
    result["_was_truncated"] = was_truncated
    return result
