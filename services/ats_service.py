import json
from services.gemini_service import ask_gemini


def analyze_resume(resume_text):

    prompt = f"""
You are an expert ATS (Applicant Tracking System) and Senior Technical Recruiter.

Analyze the following resume carefully.

IMPORTANT ATS SCORING RULES:

1. Calculate a realistic ATS score from 0 to 100.
2. The ATS score must be an INTEGER.
3. Do NOT automatically return 0.
4. Return 0 ONLY if the resume is completely empty, unreadable,
   or contains virtually no useful information.
5. If the resume contains skills, education, projects, experience,
   certifications, or other useful information, the score MUST be
   greater than 0.
6. Evaluate the score using these factors:
   - Relevant technical skills and keywords: 25 points
   - Projects and practical experience: 20 points
   - Work/internship experience: 20 points
   - Education and certifications: 15 points
   - Resume structure and clarity: 10 points
   - Achievements and measurable results: 10 points

The final score must be between 0 and 100.

For example:
- Very weak/mostly empty resume: 10-30
- Basic student resume with some skills/projects: 40-60
- Good student/graduate resume: 60-75
- Strong relevant resume: 75-90
- Excellent highly relevant resume: 90-100

Do not give a high score simply because many technologies are listed.
Evaluate the actual evidence in the resume.

Return ONLY valid JSON.

Do NOT use markdown.

Do NOT write explanations outside the JSON.

Return exactly this JSON structure:

{{
    "ats_score": 65,
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

IMPORTANT:
- Replace 65 with the actual calculated ATS score.
- Do not always return 65.
- Do not always return 0.
- ats_score must be an integer between 0 and 100.
- strengths must contain exactly 3 useful points.
- weaknesses must contain exactly 3 useful points.
- keywords should contain relevant skills/technologies/terms found in the resume.
- suggestions must contain exactly 3 useful improvement suggestions.

Resume:

{resume_text}
"""

    response = ask_gemini(prompt)

    print("\n========== AI RESPONSE ==========\n")
    print(response)
    print("\n=================================\n")

    try:
        # Remove markdown code fences if the AI accidentally adds them
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

        result = json.loads(response)

        # ---------------------------------------------------------
        # Validate ATS score
        # ---------------------------------------------------------

        score = result.get("ats_score", 0)

        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0

        # Keep score within valid ATS range
        score = max(0, min(100, score))

        result["ats_score"] = score

        # ---------------------------------------------------------
        # Make sure all required fields exist
        # ---------------------------------------------------------

        result.setdefault("strengths", [])
        result.setdefault("weaknesses", [])
        result.setdefault("keywords", [])
        result.setdefault("suggestions", [])

        print(f"✅ ATS score generated: {score}/100")

        return result

    except Exception as e:

        print("JSON ERROR:", e)
        print("RAW AI RESPONSE:")
        print(response)

        return {
            "ats_score": 0,
            "strengths": [],
            "weaknesses": [],
            "keywords": [],
            "suggestions": []
        }