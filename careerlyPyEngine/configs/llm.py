# config/llm.py

import os
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Load API key
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(
    model_name="gemma2-9b-it",
    temperature=0.4,
    api_key=groq_api_key,
)

# Shared parser
json_parser = JsonOutputParser()

def run_llm(prompt_template: ChatPromptTemplate, input_data: dict):
    """
    Runs a LangChain pipeline using the given prompt and input data.
    """
    chain = prompt_template | llm | json_parser
    return chain.invoke(input_data)
