from rest_framework.decorators import api_view
from rest_framework.response import Response
from careerlyPyEngine.configs.llm import run_llm
from careerlyPyEngine.configs.prompts.health import healthcare_prompt
import json
from django.core.cache import cache
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
        
        cache_key = f"health_conversation_{user_id}"
        conversation_data = cache.get(cache_key, {})
        
        # Initialize conversation if empty
        if not conversation_data:
            conversation_data = {
                'stage': 'initial_questions',
                'initial_info': {},
                'conversation_history': []
            }
            cache.set(cache_key, conversation_data, timeout=1800)
            return Response({
                "next_question": "To provide accurate medical advice, I first need some basic information. How old are you?",
                "information_required": True
            })

        # Debug print current state
        print(f"Current conversation state: {conversation_data}")

        # Handle initial information collection
        if conversation_data['stage'] == 'initial_questions':
            # Store the user's response
            if user_message:
                conversation_data['conversation_history'].append({
                    'user': user_message,
                    'ai': None  # Will be set when we send next question
                })
                
                # Determine which question we're on
                questions_asked = len([m for m in conversation_data['conversation_history'] 
                                     if m.get('ai') is not None])
                
                if questions_asked == 0:
                    # Just received age
                    conversation_data['initial_info']['age'] = user_message
                    next_q = "What country or region are you currently in?"
                elif questions_asked == 1:
                    # Just received region
                    conversation_data['initial_info']['region'] = user_message
                    next_q = "What is your approximate weight?"
                elif questions_asked == 2:
                    # Just received weight
                    conversation_data['initial_info']['weight'] = user_message
                    conversation_data['stage'] = 'symptom_analysis'
                    next_q = "Thank you. Now, please describe your symptoms to begin."
                
                # Update the last AI response
                if conversation_data['conversation_history']:
                    conversation_data['conversation_history'][-1]['ai'] = next_q
                
                # Save and return next question
                cache.set(cache_key, conversation_data, timeout=1800)
                return Response({
                    "next_question": next_q,
                    "information_required": conversation_data['stage'] == 'initial_questions'
                })

        # Handle symptom analysis phase
        if conversation_data['stage'] == 'symptom_analysis':
            # Add new message to history
            if user_message:
                conversation_data['conversation_history'].append({
                    'user': user_message,
                    'ai': None  # Will be set by AI response
                })

            # Format full conversation history for LLM
            formatted_history = "\n".join(
                [f"User: {item['user']}\nAI: {item['ai']}" 
                 for item in conversation_data['conversation_history'] 
                 if item['ai'] is not None or 'user' in item]
            )

            # Get LLM response
            llm_response = run_llm(
                prompt_template=healthcare_prompt,
                input_data={
                    "new_message": user_message,
                    "history": formatted_history,
                    "initial_info": conversation_data['initial_info']
                }
            )

            # Parse response
            try:
                response_data = json.loads(llm_response) if isinstance(llm_response, str) else llm_response
                
                # Build API response
                if response_data.get("diagnosis_ready"):
                    api_response = {
                        "userId": user_id,
                        "conversation_complete": True,
                        "diagnosis": {k: int(v.strip('%')) if isinstance(v, str) else int(v)
                                     for k, v in response_data.get("diagnosis", {}).items()},
                        "confidence": {k: "High" if v > 0.7 else "Moderate" if v > 0.4 else "Low"
                                      for k, v in response_data.get("confidence_levels", {}).items()},
                        "actions": response_data.get("recommendations", [])
                    }
                    cache.delete(cache_key)
                else:
                    api_response = {
                        "userId": user_id,
                        "conversation_complete": False,
                        "next_question": response_data.get("next_question", 
                                         "Can you describe your symptoms in more detail?")
                    }
                    # Store AI response in history
                    if user_message and conversation_data['conversation_history']:
                        conversation_data['conversation_history'][-1]['ai'] = api_response["next_question"]
                    cache.set(cache_key, conversation_data, timeout=1800)

                return Response(api_response)

            except Exception as e:
                return Response({"error": f"AI response parsing error: {str(e)}"}, status=500)

        return Response({"error": "Invalid conversation state"}, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=500)