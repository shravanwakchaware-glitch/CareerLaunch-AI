import uuid
import json
import re

from services.gemini_service import (
    ask_gemini,
    evaluate_with_gemini
)


class InterviewAI:

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, username, role, skills, difficulty):

        self.session_id = str(uuid.uuid4())

        self.username = username
        self.role = role
        self.skills = skills
        self.difficulty = difficulty

        # -----------------------------------------------------
        # Interview control
        # -----------------------------------------------------

        self.question_number = 1
        self.total_questions = 15

        # -----------------------------------------------------
        # Interview history
        # -----------------------------------------------------

        self.questions = []
        self.answers = []

        # -----------------------------------------------------
        # IMPORTANT
        #
        # We intentionally DO NOT use GeminiChat here.
        #
        # Every question gets a fresh, controlled prompt.
        # Python decides the round.
        # -----------------------------------------------------

    # =========================================================
    # ROUND DETECTION
    # =========================================================

    def _get_round(self, question_number):

        if 1 <= question_number <= 5:
            return "aptitude"

        elif 6 <= question_number <= 10:
            return "coding"

        elif 11 <= question_number <= 15:
            return "hr"

        raise ValueError(
            f"Invalid question number: {question_number}"
        )

    # =========================================================
    # PREVIOUS QUESTION HISTORY
    # =========================================================

    def _get_previous_questions(self):

        if not self.questions:
            return "No previous questions."

        history = ""

        for index, question in enumerate(
            self.questions,
            start=1
        ):

            history += (
                f"\nQuestion {index}: "
                f"{question}\n"
            )

        return history

    # =========================================================
    # APTITUDE VALIDATION
    # =========================================================

    def _validate_aptitude(self, question):

        if not question:
            return False

        text = question.strip()

        # -----------------------------------------------------
        # Must contain A, B, C and D
        # -----------------------------------------------------

        option_a = re.search(
            r"(?m)^\s*A[\.\):\-]",
            text,
            re.IGNORECASE
        )

        option_b = re.search(
            r"(?m)^\s*B[\.\):\-]",
            text,
            re.IGNORECASE
        )

        option_c = re.search(
            r"(?m)^\s*C[\.\):\-]",
            text,
            re.IGNORECASE
        )

        option_d = re.search(
            r"(?m)^\s*D[\.\):\-]",
            text,
            re.IGNORECASE
        )

        if not all([
            option_a,
            option_b,
            option_c,
            option_d
        ]):
            return False

        # -----------------------------------------------------
        # Must NOT look like coding
        # -----------------------------------------------------

        coding_words = [
            "write a program",
            "write code",
            "code in python",
            "code in java",
            "implement",
            "array",
            "linked list",
            "binary search",
            "palindrome",
            "algorithm",
            "function",
            "class ",
            "programming"
        ]

        lower = text.lower()

        if any(
            word in lower
            for word in coding_words
        ):
            return False

        # -----------------------------------------------------
        # Must NOT look like HR
        # -----------------------------------------------------

        hr_words = [
            "tell me about yourself",
            "your strengths",
            "your weakness",
            "where do you see yourself",
            "why should we hire",
            "career goal",
            "team conflict",
            "workplace"
        ]

        if any(
            word in lower
            for word in hr_words
        ):
            return False

        return True

    # =========================================================
    # CODING VALIDATION
    # =========================================================

    def _validate_coding(self, question):

        if not question:
            return False

        text = question.strip()
        lower = text.lower()

        # -----------------------------------------------------
        # Coding question must NOT contain MCQ options
        # -----------------------------------------------------

        options = [
            re.search(
                r"(?m)^\s*A[\.\):\-]",
                text,
                re.IGNORECASE
            ),
            re.search(
                r"(?m)^\s*B[\.\):\-]",
                text,
                re.IGNORECASE
            ),
            re.search(
                r"(?m)^\s*C[\.\):\-]",
                text,
                re.IGNORECASE
            ),
            re.search(
                r"(?m)^\s*D[\.\):\-]",
                text,
                re.IGNORECASE
            )
        ]

        # If 2 or more MCQ options are detected,
        # reject it.

        if sum(
            option is not None
            for option in options
        ) >= 2:

            return False

        # -----------------------------------------------------
        # Reject obvious aptitude questions
        # -----------------------------------------------------

        aptitude_words = [
            "profit and loss",
            "simple interest",
            "compound interest",
            "time and work",
            "time, speed",
            "percentage",
            "probability",
            "permutation",
            "combination",
            "ratio and proportion",
            "average",
            "a shopkeeper",
            "discount"
        ]

        if any(
            word in lower
            for word in aptitude_words
        ):
            return False

        # -----------------------------------------------------
        # Reject obvious HR questions
        # -----------------------------------------------------

        hr_words = [
            "tell me about yourself",
            "your strengths",
            "your weakness",
            "why should we hire",
            "where do you see yourself",
            "career goal",
            "handle conflict",
            "workplace"
        ]

        if any(
            word in lower
            for word in hr_words
        ):
            return False

        # -----------------------------------------------------
        # Must have coding/DSA characteristics
        # -----------------------------------------------------

        coding_words = [
            "write",
            "code",
            "program",
            "implement",
            "array",
            "string",
            "linked list",
            "stack",
            "queue",
            "tree",
            "graph",
            "algorithm",
            "function",
            "sort",
            "search",
            "palindrome",
            "duplicate",
            "frequency",
            "complexity"
        ]

        if not any(
            word in lower
            for word in coding_words
        ):
            return False

        return True

    # =========================================================
    # HR VALIDATION
    # =========================================================

    def _validate_hr(self, question):

        if not question:
            return False

        text = question.strip()
        lower = text.lower()

        # -----------------------------------------------------
        # HR must NOT have MCQ options
        # -----------------------------------------------------

        options = [
            re.search(
                r"(?m)^\s*A[\.\):\-]",
                text,
                re.IGNORECASE
            ),
            re.search(
                r"(?m)^\s*B[\.\):\-]",
                text,
                re.IGNORECASE
            ),
            re.search(
                r"(?m)^\s*C[\.\):\-]",
                text,
                re.IGNORECASE
            ),
            re.search(
                r"(?m)^\s*D[\.\):\-]",
                text,
                re.IGNORECASE
            )
        ]

        if sum(
            option is not None
            for option in options
        ) >= 2:

            return False

        # -----------------------------------------------------
        # Reject aptitude
        # -----------------------------------------------------

        aptitude_words = [
            "percentage",
            "profit and loss",
            "simple interest",
            "compound interest",
            "time and work",
            "probability",
            "ratio",
            "average",
            "speed and distance"
        ]

        if any(
            word in lower
            for word in aptitude_words
        ):
            return False

        # -----------------------------------------------------
        # Reject coding
        # -----------------------------------------------------

        coding_words = [
            "write a program",
            "write code",
            "implement",
            "array",
            "linked list",
            "binary search",
            "palindrome",
            "algorithm",
            "programming"
        ]

        if any(
            word in lower
            for word in coding_words
        ):
            return False

        # -----------------------------------------------------
        # Reject AI trying to end interview
        # -----------------------------------------------------

        ending_words = [
            "interview is complete",
            "interview is over",
            "no more questions",
            "question 16",
            "interview is closed",
            "this concludes the interview"
        ]

        if any(
            word in lower
            for word in ending_words
        ):
            return False

        return True

    # =========================================================
    # DUPLICATE QUESTION CHECK
    # =========================================================

    def _is_duplicate(self, question):

        if not question:
            return True

        new_question = question.lower().strip()

        for old_question in self.questions:

            old = old_question.lower().strip()

            # Exact duplicate
            if new_question == old:
                return True

            # Compare first 100 characters
            if (
                len(new_question) > 60
                and len(old) > 60
                and new_question[:100] == old[:100]
            ):
                return True

        return False

    # =========================================================
    # VALIDATE GENERATED QUESTION
    # =========================================================

    def _validate_question(
        self,
        question,
        question_number
    ):

        if not question:
            return False

        if self._is_duplicate(question):
            print(
                "⚠️ AI generated a duplicate question."
            )

            return False

        round_type = self._get_round(
            question_number
        )

        if round_type == "aptitude":

            valid = self._validate_aptitude(
                question
            )

        elif round_type == "coding":

            valid = self._validate_coding(
                question
            )

        else:

            valid = self._validate_hr(
                question
            )

        if not valid:

            print(
                f"⚠️ AI generated an INVALID "
                f"{round_type} question for Q{question_number}."
            )

            return False

        return True

    # =========================================================
    # FALLBACK QUESTIONS
    #
    # These guarantee that the interview never gets stuck
    # because the AI generated the wrong question type.
    # =========================================================

    def _fallback_question(
        self,
        question_number
    ):

        # -----------------------------------------------------
        # APTITUDE
        # -----------------------------------------------------

        aptitude_questions = {

            1: """
Question 1

A train travels 60% of a journey at 40 km/h and the
remaining 40% at 60 km/h. What is the average speed for
the entire journey?

A. 46 km/h
B. 47.5 km/h
C. 48 km/h
D. 50 km/h

Answer using A, B, C or D only.
""",

            2: """
Question 2

A shopkeeper marks an article 40% above its cost price
and gives a discount of 10%. If the selling price is
₹1,260, what is the cost price?

A. ₹900
B. ₹1,000
C. ₹1,100
D. ₹1,200

Answer using A, B, C or D only.
""",

            3: """
Question 3

A can complete a piece of work in 12 days and B can
complete it in 18 days. If they work together for 4 days,
what fraction of the work remains?

A. 1/3
B. 4/9
C. 5/9
D. 2/3

Answer using A, B, C or D only.
""",

            4: """
Question 4

The ratio of boys to girls in a class is 5:3. If 16 more
girls join the class, the ratio becomes 5:4. How many
students were originally in the class?

A. 48
B. 64
C. 72
D. 80

Answer using A, B, C or D only.
""",

            5: """
Question 5

A sum of money becomes ₹12,100 in two years at 10% per
annum compound interest. What was the principal amount?

A. ₹9,000
B. ₹10,000
C. ₹11,000
D. ₹12,000

Answer using A, B, C or D only.
"""
        }

        if question_number in aptitude_questions:

            return aptitude_questions[
                question_number
            ].strip()

        # -----------------------------------------------------
        # CODING
        # -----------------------------------------------------

        coding_questions = {

            6: """
Question 6

Write a program to find the second largest element
in an integer array.

Explain your approach and provide the code.
""",

            7: """
Question 7

Write a program to check whether a given string is a
palindrome.

Explain your approach and provide the code.
""",

            8: """
Question 8

Write a program to find the first non-repeating
character in a string.

Explain your approach and provide the code.
""",

            9: """
Question 9

Write a program to implement binary search on a
sorted integer array.

Explain the approach and provide the code.
""",

            10: """
Question 10

Write a program to remove duplicate elements from
an integer array while preserving the original order.

Explain your approach and provide the code.
"""
        }

        if question_number in coding_questions:

            return coding_questions[
                question_number
            ].strip()

        # -----------------------------------------------------
        # HR
        # -----------------------------------------------------

        hr_questions = {

            11: """
Question 11

Tell me about yourself and your background.
""",

            12: """
Question 12

Tell me about a time when you had to learn a new
technology or process quickly. How did you handle it?
""",

            13: """
Question 13

Tell me about a time you worked with a difficult
team member. How did you handle the situation?
""",

            14: """
Question 14

What is one weakness you are currently working on,
and what are you doing to improve it?
""",

            15: """
Question 15

Why should we hire you for this role?
"""
        }

        if question_number in hr_questions:

            return hr_questions[
                question_number
            ].strip()

        raise ValueError(
            f"No fallback question for Q{question_number}"
        )

    # =========================================================
    # BUILD PROMPT FOR APTITUDE
    # =========================================================

    def _build_aptitude_prompt(
        self,
        question_number,
        attempt
    ):

        previous = self._get_previous_questions()

        return f"""
YOU ARE THE QUESTION GENERATION ENGINE FOR CAREERLAUNCH AI.

THIS IS A STRICT PROGRAMMING CONTRACT.

PYTHON HAS ALREADY DECIDED:

CURRENT QUESTION NUMBER = {question_number}

CURRENT ROUND = APTITUDE

YOU MUST OBEY PYTHON.

DO NOT CHANGE THE QUESTION NUMBER.
DO NOT CHANGE THE ROUND.
DO NOT SKIP A QUESTION.
DO NOT CREATE QUESTION {question_number + 1}.
DO NOT CREATE QUESTION 16.
DO NOT END THE INTERVIEW.
DO NOT EVALUATE THE CANDIDATE.

THIS IS ATTEMPT {attempt}.

If you violate ANY rule below, your response will be rejected
by the application.

============================================================
APTITUDE REQUIREMENTS
============================================================

Generate EXACTLY ONE college placement-level aptitude MCQ.

It must:

1. Require reasoning or multiple steps.
2. NOT be trivial arithmetic.
3. Have EXACTLY four options.
4. Use exactly A, B, C and D.
5. Have exactly ONE correct option.
6. NEVER reveal the correct answer.
7. Ask the candidate to answer A, B, C or D.
8. NOT be a coding question.
9. NOT be an HR question.
10. NOT be a technical theory question.
11. NOT contain multiple questions.
12. NOT repeat a previous question.

Suitable topics:

- Percentages
- Profit and Loss
- Simple Interest
- Compound Interest
- Time and Work
- Time, Speed and Distance
- Ratio
- Averages
- Probability
- Permutation and Combination
- Number Systems
- Logical Reasoning
- Data Interpretation

============================================================
OUTPUT FORMAT
============================================================

Question {question_number}

[Question]

A. [Option]
B. [Option]
C. [Option]
D. [Option]

Answer using A, B, C or D only.

DO NOT provide the correct answer.

============================================================
PREVIOUS QUESTIONS
============================================================

{previous}
"""

    # =========================================================
    # BUILD PROMPT FOR CODING
    # =========================================================

    def _build_coding_prompt(
        self,
        question_number,
        attempt
    ):

        previous = self._get_previous_questions()

        return f"""
YOU ARE THE QUESTION GENERATION ENGINE FOR CAREERLAUNCH AI.

THIS IS A STRICT PROGRAMMING CONTRACT.

PYTHON HAS ALREADY DECIDED:

CURRENT QUESTION NUMBER = {question_number}

CURRENT ROUND = TECHNICAL / CODING

YOU MUST OBEY PYTHON.

DO NOT CHANGE THE QUESTION NUMBER.
DO NOT CHANGE THE ROUND.
DO NOT SKIP A QUESTION.
DO NOT CREATE QUESTION {question_number + 1}.
DO NOT CREATE QUESTION 16.
DO NOT END THE INTERVIEW.
DO NOT EVALUATE THE CANDIDATE.

THIS IS ATTEMPT {attempt}.

If you violate ANY rule below, your response will be rejected
by the application.

============================================================
CODING REQUIREMENTS
============================================================

Generate EXACTLY ONE small DSA/programming problem.

Candidate role:
{self.role}

Candidate skills:
{", ".join(self.skills)}

Difficulty:
{self.difficulty}

The candidate must write code and/or explain the algorithm.

Suitable topics:

- Arrays
- Strings
- Searching
- Sorting
- Hashing
- Linked Lists
- Stacks
- Queues
- Basic Trees
- Basic Algorithms

Examples:

- Reverse an array
- Find second largest element
- Check palindrome
- Find duplicate elements
- Binary search
- Find missing number
- Character frequency
- Remove duplicates
- Maximum subarray
- Reverse linked list
- Balanced parentheses

============================================================
ABSOLUTE RESTRICTIONS
============================================================

DO NOT create an aptitude question.

DO NOT ask:

- percentages
- profit and loss
- simple interest
- compound interest
- time and work
- probability
- ratio
- average
- speed and distance

DO NOT use A/B/C/D options.

DO NOT create an HR question.

DO NOT provide the solution.

DO NOT provide code yourself.

DO NOT ask multiple questions.

DO NOT evaluate the candidate.

============================================================
OUTPUT FORMAT
============================================================

Question {question_number}

[Small DSA / coding problem]

Ask the candidate to write code and/or explain the approach.

============================================================
PREVIOUS QUESTIONS
============================================================

{previous}
"""

    # =========================================================
    # BUILD PROMPT FOR HR
    # =========================================================

    def _build_hr_prompt(
        self,
        question_number,
        attempt
    ):

        previous = self._get_previous_questions()

        return f"""
YOU ARE THE QUESTION GENERATION ENGINE FOR CAREERLAUNCH AI.

THIS IS A STRICT PROGRAMMING CONTRACT.

PYTHON HAS ALREADY DECIDED:

CURRENT QUESTION NUMBER = {question_number}

CURRENT ROUND = HR / BEHAVIORAL

YOU MUST OBEY PYTHON.

DO NOT CHANGE THE QUESTION NUMBER.
DO NOT CHANGE THE ROUND.
DO NOT SKIP A QUESTION.
DO NOT CREATE QUESTION {question_number + 1}.
DO NOT CREATE QUESTION 16.
DO NOT END THE INTERVIEW BEFORE THE CANDIDATE ANSWERS
QUESTION {question_number}.

THIS IS ATTEMPT {attempt}.

If you violate ANY rule below, your response will be rejected
by the application.

============================================================
HR REQUIREMENTS
============================================================

Generate EXACTLY ONE HR / behavioral interview question.

Candidate role:
{self.role}

Suitable topics:

- Self introduction
- Strengths
- Weaknesses
- Teamwork
- Leadership
- Conflict resolution
- Handling pressure
- Failure
- Learning
- Career goals
- Motivation
- Adaptability
- Why should we hire you?

============================================================
ABSOLUTE RESTRICTIONS
============================================================

DO NOT create an aptitude question.

DO NOT create a coding question.

DO NOT use A/B/C/D options.

DO NOT provide an answer.

DO NOT evaluate the candidate.

DO NOT ask multiple questions.

DO NOT say:

- "The interview is complete"
- "The interview is over"
- "There are no more questions"
- "Question 16"
- "The interview is closed"

DO NOT repeat a previous question.

============================================================
OUTPUT FORMAT
============================================================

Question {question_number}

[ONE HR QUESTION]

============================================================
PREVIOUS QUESTIONS
============================================================

{previous}
"""

    # =========================================================
    # GENERATE QUESTION
    # =========================================================

    def _generate_question(
        self,
        question_number
    ):

        # -----------------------------------------------------
        # Never allow invalid question numbers
        # -----------------------------------------------------

        if question_number < 1:

            raise ValueError(
                "Question number cannot be less than 1."
            )

        if question_number > self.total_questions:

            raise ValueError(
                "Question 16 or higher is not allowed."
            )

        round_type = self._get_round(
            question_number
        )

        print()
        print("=" * 60)
        print(
            f"GENERATING QUESTION {question_number}"
        )
        print(
            f"ROUND: {round_type.upper()}"
        )
        print("=" * 60)

        # -----------------------------------------------------
        # Try AI up to 3 times
        # -----------------------------------------------------

        for attempt in range(1, 4):

            print(
                f"🤖 AI generation attempt "
                f"{attempt}/3"
            )

            if round_type == "aptitude":

                prompt = self._build_aptitude_prompt(
                    question_number,
                    attempt
                )

            elif round_type == "coding":

                prompt = self._build_coding_prompt(
                    question_number,
                    attempt
                )

            else:

                prompt = self._build_hr_prompt(
                    question_number,
                    attempt
                )

            try:

                question = ask_gemini(
                    prompt
                )

                question = question.strip()

                print(
                    "AI generated:"
                )

                print(
                    question
                )

                # -------------------------------------------------
                # Validate
                # -------------------------------------------------

                if self._validate_question(
                    question,
                    question_number
                ):

                    print(
                        f"✅ Q{question_number} "
                        f"passed validation."
                    )

                    return question

                print(
                    f"❌ Q{question_number} "
                    f"failed validation."
                )

            except Exception as e:

                print(
                    f"⚠️ AI generation error: {e}"
                )

        # -----------------------------------------------------
        # AI failed validation 3 times.
        #
        # Use deterministic fallback so the interview
        # NEVER breaks or jumps to another round.
        # -----------------------------------------------------

        print()
        print(
            f"⚠️ AI failed to generate a valid "
            f"Q{question_number}."
        )

        print(
            "🔒 Using safe fallback question."
        )

        fallback = self._fallback_question(
            question_number
        )

        return fallback

    # =========================================================
    # START INTERVIEW
    # =========================================================

    def start_interview(self):

        # Python explicitly starts at Q1.

        self.question_number = 1

        question = self._generate_question(
            1
        )

        # -----------------------------------------------------
        # Python controls the round announcement.
        #
        # The AI does NOT generate this anymore.
        # -----------------------------------------------------

        question = (
            "Let's begin with the Aptitude Round.\n\n"
            + question
        )

        self.questions.append(
            question
        )

        print()
        print("=" * 60)
        print("INTERVIEW STARTED")
        print("Question Number:", self.question_number)
        print("Questions Stored:", len(self.questions))
        print("Answers Stored:", len(self.answers))
        print("=" * 60)

        return {
            "session_id": self.session_id,
            "question_number": self.question_number,
            "question": question
        }

    # =========================================================
    # SUBMIT ANSWER
    # =========================================================

    def submit_answer(self, answer):

        # -----------------------------------------------------
        # Make sure interview is still active
        # -----------------------------------------------------

        if self.question_number > self.total_questions:

            raise RuntimeError(
                "The interview has already been completed."
            )

        # -----------------------------------------------------
        # Save answer
        # -----------------------------------------------------

        answer = (answer or "").strip()

        self.answers.append(
            answer
        )

        print()
        print("=" * 60)
        print("ANSWER RECEIVED")
        print(
            "Question Number:",
            self.question_number
        )
        print(
            "Questions Stored:",
            len(self.questions)
        )
        print(
            "Answers Stored:",
            len(self.answers)
        )
        print("=" * 60)

        # -----------------------------------------------------
        # Q15 answered
        #
        # DO NOT increment to Q16.
        # -----------------------------------------------------

        if self.question_number == self.total_questions:

            print()
            print("=" * 60)
            print("INTERVIEW FINISHED")
            print(
                "Questions:",
                len(self.questions)
            )
            print(
                "Answers:",
                len(self.answers)
            )
            print(
                "Question Number:",
                self.question_number
            )
            print("=" * 60)

            return self._finish_interview()

        # -----------------------------------------------------
        # Move to EXACTLY next question
        # -----------------------------------------------------

        next_question_number = (
            self.question_number + 1
        )

        # Safety check

        if next_question_number > self.total_questions:

            raise RuntimeError(
                "Attempted to generate Question 16."
            )

        self.question_number = (
            next_question_number
        )

        print()
        print("=" * 60)
        print(
            "NEXT QUESTION:",
            self.question_number
        )
        print(
            "ROUND:",
            self._get_round(
                self.question_number
            ).upper()
        )
        print("=" * 60)

        # -----------------------------------------------------
        # Generate exact next question
        # -----------------------------------------------------

        question = self._generate_question(
            self.question_number
        )

        # -----------------------------------------------------
        # Python controls round announcements.
        # -----------------------------------------------------

        if self.question_number == 6:

            question = (
                "Great! The Technical and Coding Round "
                "will now begin.\n\n"
                + question
            )

        elif self.question_number == 11:

            question = (
                "Great! The HR Round will now begin.\n\n"
                + question
            )

        self.questions.append(
            question
        )

        print()
        print(
            "Questions Stored:",
            len(self.questions)
        )

        print(
            "Answers Stored:",
            len(self.answers)
        )

        return {
            "finished": False,
            "question_number": self.question_number,
            "question": question
        }

    # =========================================================
    # FINISH INTERVIEW
    # =========================================================

    def _finish_interview(self):

        # -----------------------------------------------------
        # Safety checks
        # -----------------------------------------------------

        if len(self.questions) != self.total_questions:

            print()
            print(
                "⚠️ WARNING: Question count is not 15."
            )

            print(
                "Questions:",
                len(self.questions)
            )

        if len(self.answers) != self.total_questions:

            print()
            print(
                "⚠️ WARNING: Answer count is not 15."
            )

            print(
                "Answers:",
                len(self.answers)
            )

        # -----------------------------------------------------
        # Build complete interview
        # -----------------------------------------------------

        interview_text = ""

        total_items = min(
            len(self.questions),
            len(self.answers)
        )

        for i in range(total_items):

            interview_text += f"""

==============================
QUESTION {i + 1}
==============================

{self.questions[i]}

CANDIDATE ANSWER

{self.answers[i]}

"""

        # -----------------------------------------------------
        # Final evaluation prompt
        # -----------------------------------------------------

        evaluation_prompt = f"""
You are an expert placement interviewer.

Evaluate the candidate's COMPLETE mock interview.

The interview structure is STRICTLY:

Questions 1-5:
APTITUDE

Questions 6-10:
TECHNICAL / CODING

Questions 11-15:
HR

Evaluate the candidate based on their actual answers.

Do not invent answers.

============================================================
SCORING
============================================================

Evaluate:

1. Overall performance
2. Aptitude performance
3. Technical/coding performance
4. HR performance
5. Communication
6. Confidence

All scores must be numbers from 0 to 100.

============================================================
JSON RULES
============================================================

Return ONLY valid JSON.

DO NOT write markdown.

DO NOT use ```json.

DO NOT write explanations outside JSON.

DO NOT add extra fields.

Return EXACTLY:

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

============================================================
COMPLETE INTERVIEW
============================================================

{interview_text}
"""

        # =====================================================
        # FINAL AI EVALUATION
        #
        # Gemini → OpenRouter → Ollama
        # =====================================================

        print()
        print("=" * 60)
        print("STARTING FINAL AI EVALUATION")
        print("Provider order:")
        print("1. Gemini")
        print("2. OpenRouter")
        print("3. Ollama")
        print("=" * 60)
        print()

        try:

            report = evaluate_with_gemini(
                evaluation_prompt,
                temperature=0.2,
                max_tokens=4096
            )

        except Exception as e:

            print()
            print("=" * 60)
            print(
                "FINAL AI EVALUATION FAILED"
            )
            print("=" * 60)
            print(e)
            print("=" * 60)
            print()

            return {
                "finished": True,
                "report": {
                    "overall_score": 0,
                    "aptitude_score": 0,
                    "technical_score": 0,
                    "hr_score": 0,
                    "communication_score": 0,
                    "confidence_score": 0,
                    "strengths": [
                        "Unable to generate evaluation."
                    ],
                    "weaknesses": [
                        "AI evaluation failed."
                    ],
                    "recommendations": [
                        "Please try the interview again."
                    ]
                }
            }

        # =====================================================
        # PARSE JSON
        # =====================================================

        try:

            print()
            print("=" * 60)
            print("RAW AI EVALUATION")
            print("=" * 60)
            print(report)
            print("=" * 60)
            print()

            report = report.strip()

            # -------------------------------------------------
            # Remove markdown fences
            # -------------------------------------------------

            report = report.replace(
                "```json",
                ""
            )

            report = report.replace(
                "```",
                ""
            )

            report = report.strip()

            # -------------------------------------------------
            # Parse JSON
            # -------------------------------------------------

            report_json = json.loads(
                report
            )

            # -------------------------------------------------
            # Required fields
            # -------------------------------------------------

            default_values = {

                "overall_score": 0,

                "aptitude_score": 0,

                "technical_score": 0,

                "hr_score": 0,

                "communication_score": 0,

                "confidence_score": 0,

                "strengths": [],

                "weaknesses": [],

                "recommendations": []

            }

            for key, default in default_values.items():

                if key not in report_json:

                    report_json[key] = default

            print("=" * 60)
            print(
                "AI EVALUATION JSON SUCCESS"
            )
            print("=" * 60)

            print(
                "Overall:",
                report_json["overall_score"]
            )

            print(
                "Aptitude:",
                report_json["aptitude_score"]
            )

            print(
                "Technical:",
                report_json["technical_score"]
            )

            print(
                "HR:",
                report_json["hr_score"]
            )

            print(
                "Communication:",
                report_json["communication_score"]
            )

            print(
                "Confidence:",
                report_json["confidence_score"]
            )

            print("=" * 60)

        except Exception as e:

            print()
            print("=" * 60)
            print("AI EVALUATION JSON ERROR")
            print("=" * 60)
            print(e)
            print()
            print("RAW AI RESPONSE:")
            print(report)
            print("=" * 60)

            report_json = {

                "overall_score": 0,

                "aptitude_score": 0,

                "technical_score": 0,

                "hr_score": 0,

                "communication_score": 0,

                "confidence_score": 0,

                "strengths": [
                    "Unable to generate evaluation."
                ],

                "weaknesses": [
                    "AI evaluation response could not be parsed."
                ],

                "recommendations": [
                    "Please try the interview again."
                ]

            }

        # -----------------------------------------------------
        # Return final result
        # -----------------------------------------------------

        return {
            "finished": True,
            "report": report_json
        }


# =============================================================
# RESUME SKILL EXTRACTION
# =============================================================

def extract_skills(resume_text):

    prompt = f"""
You are an AI Resume Analyzer.

Extract ONLY the technical skills from the resume.

Return ONLY valid JSON.

Use exactly this format:

{{
    "skills": [
        "Python",
        "Flask",
        "SQL",
        "Machine Learning"
    ]
}}

Resume:

{resume_text}
"""

    response = ask_gemini(
        prompt
    )

    try:

        response = response.replace(
            "```json",
            ""
        )

        response = response.replace(
            "```",
            ""
        )

        response = response.strip()

        data = json.loads(
            response
        )

        return data.get(
            "skills",
            []
        )

    except Exception:

        return []


# =============================================================
# ACTIVE INTERVIEW SESSIONS
# =============================================================

active_interviews = {}