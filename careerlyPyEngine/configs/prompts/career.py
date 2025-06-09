# prompts/career.py

from langchain_core.prompts import ChatPromptTemplate

career_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a career guidance assistant.

Given a user's education history and skill set, your task is to suggest one realistic and promising career path. Base it on job market relevance, user background, and current trends.

📥 Input Format:
- Education includes field, degree level, and institution.
- Skills are general or technical competencies.

🎯 Output Format (JSON only):
{{
  "career_path": "One clear career title (e.g., 'Cloud Engineer', 'Frontend Developer')"
}}"""
    ),
    (
        "user",
        """Education: {education}
Skills: {skills}

Suggest the most relevant career path. Output JSON only."""
    )
])
