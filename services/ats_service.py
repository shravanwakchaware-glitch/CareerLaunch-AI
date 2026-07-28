import json
from services.gemini_service import ask_gemini


def analyze_resume(resume_text):

    prompt = f"""
You are an expert ATS (Applicant Tracking System) and Senior Technical Recruiter.

Analyze the following resume.

Return ONLY valid JSON.

Do NOT use markdown.
Do NOT write explanations.

Return exactly in this format:

{{
    "ats_score": 0,
    "strengths": [
        "...",
        "...",
        "..."
    ],
    "weaknesses": [
        "...",
        "...",
        "..."
    ],
    "keywords": [
        "...",
        "...",
        "..."
    ],
    "suggestions": [
        {{
            "title": "...",
            "description": "..."
        }},
        {{
            "title": "...",
            "description": "..."
        }},
        {{
            "title": "...",
            "description": "..."
        }}
    ]
}}

Resume:

{resume_text}
"""

    response = ask_gemini(prompt)

    print("\n========== GEMINI RESPONSE ==========\n")
    print(response)
    print("\n=====================================\n")

    try:
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

        return json.loads(response)

    except Exception as e:

        print("JSON ERROR:", e)

        return {
            "ats_score": 0,
            "strengths": [],
            "weaknesses": [],
            "keywords": [],
            "suggestions": []
        }