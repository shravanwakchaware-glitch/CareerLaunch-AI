import uuid

from services.gemini_service import GeminiChat


class InterviewAI:

    def __init__(self, username, role, skills, difficulty):

        self.session_id = str(uuid.uuid4())

        self.username = username
        self.role = role
        self.skills = skills
        self.difficulty = difficulty

        self.question_number = 1
        self.total_questions = 2

        # Store interview history
        self.questions = []
        self.answers = []

        self.system_prompt = f"""
You are an experienced placement interviewer.

Candidate Name: {username}

Job Role: {role}

Skills: {", ".join(skills)}

Difficulty: {difficulty}

Interview Structure:

Round 1
Questions 1-5
Aptitude only

Round 2
Questions 6-10
Technical only

Round 3
Questions 11-15
HR only

Rules:

1. Ask ONLY one question at a time.

2. Never ask for role or skills again.

3. Wait for the candidate's answer.

4. Do NOT evaluate until all 15 questions are complete.

5. Keep questions concise.

6. Remember previous answers.

7. After Question 15, wait for another prompt requesting the final evaluation.
"""

        self.chat = GeminiChat(self.system_prompt)

    def start_interview(self):

        question = self.chat.send("Begin the interview.")

        self.questions.append(question)

        return {
            "session_id": self.session_id,
            "question_number": self.question_number,
            "question": question
        }

    def submit_answer(self, answer):

        # Save current answer
        self.answers.append(answer)

        self.question_number += 1

        # Continue interview
        if self.question_number <= self.total_questions:

            prompt = f"""
Candidate's Answer:

{answer}

Now ask ONLY Question {self.question_number}.

Do not give any explanation.
Do not evaluate the answer.
Do not ask multiple questions.
"""

            question = self.chat.send(prompt)

            self.questions.append(question)

            return {
                "finished": False,
                "question_number": self.question_number,
                "question": question
            }

        # Interview Finished
        else:

            interview_text = ""

            for i in range(len(self.answers)):

                interview_text += f"""

Question {i+1}

{self.questions[i]}

Candidate Answer

{self.answers[i]}

"""

            evaluation_prompt = f"""
You are an expert placement interviewer.

Evaluate the complete interview below.

Return ONLY valid JSON.

Do NOT write markdown.

Do NOT write explanations.

Return exactly this format:

{{
    "overall_score": 0,
    "aptitude_score": 0,
    "technical_score": 0,
    "hr_score": 0,
    "communication_score": 0,
    "confidence_score": 0,
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
    "recommendations": [
        "...",
        "...",
        "..."
    ]
}}

Interview:

{interview_text}
"""

            report = self.chat.send(evaluation_prompt)

            return {
                "finished": True,
                "report": report
            }


# Store all active interview sessions
active_interviews = {}