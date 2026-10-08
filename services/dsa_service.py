import json
import re

from services.gemini_service import evaluate_with_gemini


# ============================================================
# DSA AI EVALUATOR
# ============================================================

def evaluate_dsa_solution(
    title,
    problem_statement,
    constraints,
    expected_time,
    expected_space,
    language,
    code
):

    prompt = f"""
You are an expert LeetCode and DSA interviewer.

Evaluate the candidate's submitted code for the given DSA problem.

============================================================
PROBLEM
============================================================

Title:
{title}

Problem Statement:
{problem_statement}

Constraints:
{constraints}

Expected Time Complexity:
{expected_time}

Expected Space Complexity:
{expected_space}


============================================================
CANDIDATE SUBMISSION
============================================================

Programming Language:
{language}

Candidate Code:

{code}


============================================================
EVALUATION RULES
============================================================

Evaluate the code based on:

1. Correctness
2. Logic
3. Whether it solves the given problem
4. Edge cases
5. Time complexity
6. Space complexity
7. Code quality

IMPORTANT:

- Do NOT execute the candidate code.
- Analyze the code logically.
- If the code is incomplete, mark it incorrect.
- If the code only contains "pass", mark it incorrect.
- If the code has syntax or logical problems, mark it incorrect.
- Do not require the candidate's code to be identical to a reference solution.
- Different valid approaches should be accepted.
- Focus on whether the solution correctly solves the problem.


============================================================
JSON OUTPUT
============================================================

Return ONLY valid JSON.

DO NOT use markdown.

DO NOT use ```json.

DO NOT write anything before or after the JSON.

Return exactly this structure:

{{
    "correct": true,
    "feedback": "Explain briefly why the solution is correct or incorrect.",
    "time_complexity": "O(n)",
    "space_complexity": "O(n)",
    "correct_approach": "Explain the correct approach briefly."
}}

The "correct" field MUST be either true or false.

The complexity fields must contain standard Big-O notation.
"""


    print()
    print("=" * 60)
    print("DSA AI EVALUATION STARTED")
    print("=" * 60)
    print("Question:", title)
    print("Language:", language)
    print("Code:")
    print(code)
    print("=" * 60)


    try:

        # ----------------------------------------------------
        # Gemini / AI provider chain
        # ----------------------------------------------------

        response = evaluate_with_gemini(
            prompt,
            temperature=0.2,
            max_tokens=1200
        )


        print()
        print("=" * 60)
        print("RAW DSA AI RESPONSE")
        print("=" * 60)
        print(response)
        print("=" * 60)


        if not response:
            raise RuntimeError(
                "AI returned an empty response."
            )


        # ----------------------------------------------------
        # Clean response
        # ----------------------------------------------------

        response = response.strip()

        response = response.replace(
            "```json",
            ""
        )

        response = response.replace(
            "```",
            ""
        )

        response = response.strip()


        # ----------------------------------------------------
        # Try direct JSON parsing
        # ----------------------------------------------------

        try:

            result = json.loads(response)

        except json.JSONDecodeError:

            # ------------------------------------------------
            # AI sometimes adds text around JSON.
            # Extract the JSON object.
            # ------------------------------------------------

            match = re.search(
                r"\{.*\}",
                response,
                re.DOTALL
            )

            if not match:

                raise RuntimeError(
                    "AI did not return valid JSON.\n"
                    f"Raw response:\n{response}"
                )


            json_text = match.group(0)

            result = json.loads(
                json_text
            )


        # ----------------------------------------------------
        # Validate required fields
        # ----------------------------------------------------

        correct = result.get(
            "correct",
            False
        )


        if isinstance(correct, str):

            correct = (
                correct.lower()
                in ["true", "yes", "correct"]
            )


        result["correct"] = bool(
            correct
        )


        result["feedback"] = result.get(
            "feedback",
            "No feedback was provided."
        )


        result["time_complexity"] = result.get(
            "time_complexity",
            "Not determined"
        )


        result["space_complexity"] = result.get(
            "space_complexity",
            "Not determined"
        )


        result["correct_approach"] = result.get(
            "correct_approach",
            ""
        )


        print()
        print("=" * 60)
        print("DSA AI EVALUATION SUCCESS")
        print("=" * 60)
        print("Correct:", result["correct"])
        print("Time:", result["time_complexity"])
        print("Space:", result["space_complexity"])
        print("=" * 60)


        return result


    except Exception as e:

        print()
        print("=" * 60)
        print("DSA AI EVALUATION ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)


        raise RuntimeError(
            f"DSA AI evaluation failed: {str(e)}"
        )