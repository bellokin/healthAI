from rest_framework.decorators import api_view
from rest_framework.response import Response

from careerlyPyEngine.configs.llm import run_llm
from careerlyPyEngine.configs.prompts.career import career_prompt


@api_view(['POST'])
def suggest_career_path(request):
    try:
        data = request.data
        user_id = data.get("userId")  # Extract userId
        education_entries = data.get("educationEntries", [])
        skills = data.get("skills", [])

        if not user_id:
            return Response({"error": "Missing userId"}, status=400)

        if not education_entries or not skills:
            return Response({"error": "Missing educationEntries or skills"}, status=400)

        education_str = ", ".join([
            f"{entry.get('level', '')} in {entry.get('field', '')} from {entry.get('institution', '')} (In Progress: {entry.get('inProgress', False)})"
            for entry in education_entries
        ])
        skills_str = ", ".join(skills)

        result = run_llm(
            prompt_template=career_prompt,
            input_data={"education": education_str, "skills": skills_str}
        )

        if "career_path" not in result:
            return Response({"error": "Model did not return a valid career path"}, status=500)

        return Response({
            "userId": user_id,
            "career_path": result["career_path"]
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
