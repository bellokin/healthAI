from rest_framework.decorators import api_view
from rest_framework.response import Response
from careerlyPyEngine.configs.llm import run_llm
from careerlyPyEngine.configs.prompts.health import healthcare_prompt
import json
from django.core.cache import cache  # For storing conversation history

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@api_view(['POST'])
def health_assistant(request):
    try:
        data = request.data
        user_id = data.get("userId")
        user_message = data.get("message", "").strip()
        
        if not user_id:
            return Response({"error": "Missing userId"}, status=400)
        
        # Get or initialize conversation history from cache
        cache_key = f"health_conversation_{user_id}"
        conversation_history = cache.get(cache_key, [])
        
        print(f"Current history for {user_id}: {conversation_history}")  # Debug log
        
        # Require initial symptoms if no existing conversation
        if not user_message and not conversation_history:
            return Response({
                "error": "Please describe your symptoms to begin",
                "example": "I have a headache and fever"
            }, status=400)

        # Add new user message to history if exists
        if user_message:
            conversation_history.append({"user": user_message, "ai": ""})

        # Format entire conversation history for LLM context
        formatted_history = "\n".join(
            [f"User: {item['user']}\nAI: {item['ai']}" 
             for item in conversation_history if item['ai'] or item['user']]  # Include all exchanges
        )

        # Get LLM response
        llm_response = run_llm(
            prompt_template=healthcare_prompt,
            input_data={
                "new_message": user_message,
                "history": formatted_history or "No prior conversation"
            }
        )

        # Parse LLM response
        try:
            response_data = json.loads(llm_response) if isinstance(llm_response, str) else llm_response
        except json.JSONDecodeError:
            response_data = {"error": "AI response format error"}

        # Update conversation with AI response
        if conversation_history and not response_data.get("error"):
            conversation_history[-1]["ai"] = response_data.get("next_question", "")
            
            # Save updated history to cache (with 30 minute timeout)
            cache.set(cache_key, conversation_history, timeout=1800)

        # Build API response
        api_response = {
            "userId": user_id,
            "conversation_complete": response_data.get("diagnosis_ready", False)
        }

        if response_data.get("diagnosis_ready"):
            api_response.update({
                "diagnosis": response_data.get("diagnosis", {}),
                "confidence": response_data.get("confidence_levels", {}),
                "actions": response_data.get("recommendations", [])
            })
            # Clear conversation history after diagnosis
            cache.delete(cache_key)
        else:
            api_response["next_question"] = response_data.get("next_question", 
                "Can you describe your symptoms in more detail?")

        return Response(api_response)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
