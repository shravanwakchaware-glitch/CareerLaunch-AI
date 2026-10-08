import json
import re

from services.gemini_service import ask_gemini


def extract_json(response):
    """
    Extract JSON from the AI response.

    Handles:
    1. Normal JSON
    2. JSON inside ```json ... ```
    3. Extra text before/after JSON
    """

    if not response:
        return None

    response = response.strip()

    # Remove markdown code fences
    response = response.replace("```json", "")
    response = response.replace("```JSON", "")
    response = response.replace("```", "")
    response = response.strip()

    # -------------------------------------------------
    # Try normal JSON first
    # -------------------------------------------------
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # -------------------------------------------------
    # Try extracting JSON object from extra text
    # -------------------------------------------------
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1 and end > start:

        json_text = response[start:end + 1]

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass

    # -------------------------------------------------
    # Regex fallback
    # -------------------------------------------------
    match = re.search(r"\{.*\}", response, re.DOTALL)

    if match:

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def evaluate_hr_answer(question, answer):

    prompt = f"""
You are an expert HR interviewer and placement evaluator.

Evaluate the candidate's answer to the HR interview question.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

Evaluate the answer based on:

1. Communication
2. Relevance
3. Confidence
4. Answer quality
5. Professionalism
6. Structure

Give scores from 0 to 100.

IMPORTANT:
Return ONLY a valid JSON object.

Do NOT use markdown.
Do NOT use ```json.
Do NOT write anything before the JSON.
Do NOT write anything after the JSON.

Return exactly this structure:

{{
    "score": 0,
    "communication": 0,
    "relevance": 0,
    "confidence": 0,
    "answer_quality": 0,
    "feedback": "...",
    "strengths": [
        "...",
        "...",
        "..."
    ],
    "improvements": [
        "...",
        "...",
        "..."
    ]
}}

Rules:

- All scores must be integers between 0 and 100.
- score is the overall answer score.
- communication evaluates clarity and language.
- relevance evaluates how directly the answer answers the question.
- confidence evaluates confidence demonstrated in the answer.
- answer_quality evaluates completeness and quality.
- feedback should be short and constructive.
- strengths must contain useful observations.
- improvements must contain useful suggestions.
- Return valid JSON only.
"""

    print("\n============================================================")
    print("HR AI EVALUATION")
    print("============================================================")
    print("Question:", question)
    print("Answer:", answer)
    print("============================================================")

    try:

        # -------------------------------------------------
        # Call Gemini
        # -------------------------------------------------
        print("\n☁️ Trying Gemini...")

        response = ask_gemini(prompt)

        print("\n========== AI RAW RESPONSE ==========")
        print(response)
        print("=====================================")

        if not response:
            raise ValueError(
                "AI returned an empty response."
            )

        # -------------------------------------------------
        # Extract JSON
        # -------------------------------------------------
        result = extract_json(response)

        if result is None:

            print("\n❌ AI returned invalid JSON.")

            raise ValueError(
                "AI returned invalid JSON."
            )

        # -------------------------------------------------
        # Required fields
        # -------------------------------------------------
        required_fields = [
            "score",
            "communication",
            "relevance",
            "confidence",
            "answer_quality",
            "feedback",
            "strengths",
            "improvements"
        ]

        for field in required_fields:

            if field not in result:

                raise ValueError(
                    f"AI response missing required field: {field}"
                )

        # -------------------------------------------------
        # Validate numeric scores
        # -------------------------------------------------
        score_fields = [
            "score",
            "communication",
            "relevance",
            "confidence",
            "answer_quality"
        ]

        for field in score_fields:

            try:
                result[field] = int(result[field])
            except (ValueError, TypeError):

                result[field] = 0

            # Keep score between 0 and 100
            result[field] = max(
                0,
                min(100, result[field])
            )

        # -------------------------------------------------
        # Validate feedback
        # -------------------------------------------------
        if not isinstance(result["feedback"], str):
            result["feedback"] = str(
                result["feedback"]
            )

        # -------------------------------------------------
        # Validate strengths
        # -------------------------------------------------
        if not isinstance(result["strengths"], list):
            result["strengths"] = []

        # -------------------------------------------------
        # Validate improvements
        # -------------------------------------------------
        if not isinstance(result["improvements"], list):
            result["improvements"] = []

        # -------------------------------------------------
        # Success
        # -------------------------------------------------
        print("\n✅ HR evaluation successful.")

        print("Score:", result["score"])
        print(
            "Communication:",
            result["communication"]
        )
        print(
            "Relevance:",
            result["relevance"]
        )
        print(
            "Confidence:",
            result["confidence"]
        )
        print(
            "Answer Quality:",
            result["answer_quality"]
        )

        return result

    except Exception as e:

        print("\n============================================================")
        print("HR AI EVALUATION ERROR")
        print("============================================================")
        print(str(e))
        print("============================================================")

        # Re-raise so /hr-submit can handle the error
        raise