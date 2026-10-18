import os
import time
import instructor
from anthropic import Anthropic
from dotenv import load_dotenv
from job_description import JobDescription
from cost_log import log_run
from pathlib import Path
from groq import Groq
from config import Model, all_models

load_dotenv()

anthropic_api_key = os.environ['ANTHROPIC_API_KEY']
groq_api_key = os.environ['GROQ_API_KEY']

# JSON mode: newer models (e.g. Opus 5.5) reject the forced tool call that the default TOOLS mode uses
anthropicClient = instructor.from_anthropic(Anthropic(api_key=anthropic_api_key), mode=instructor.Mode.ANTHROPIC_JSON)
groqClient = instructor.from_groq(Groq(api_key=groq_api_key))

all_model_Ids = [
    modelDetails['modelId']
    for model in all_models.values()
    for modelDetails in model.values()
]

def extract_job_description(jd_text: str, model: Model, modelId: str) -> JobDescription:
    # token counter: instructor calls count_tokens() after EVERY API response (retries too)
    if model not in Model:
        raise ValueError(f"Invalid Model: {model}")
    if modelId not in all_model_Ids:
        raise ValueError(f"Invalid modelId: {modelId}")

    if model == Model.ANTHROPIC:
        client = anthropicClient
    else:
        client = groqClient

    
    usage = {"attempts": 0, "input": 0, "output": 0}

    def count_tokens(response):
        u = response.usage
        usage["attempts"] += 1
        usage["input"] += getattr(u, "input_tokens", None) or u.prompt_tokens
        usage["output"] += getattr(u, "output_tokens", None) or u.completion_tokens

    client.on("completion:response", count_tokens)

    prompt = (
        "Extract the structured details from the job description below.\n\n"
        f"<job_description>\n{jd_text}\n</job_description>"
    )
    try:
        result = client.messages.create(
            model=modelId,
            max_tokens=2048,
            max_retries=3,
            messages=[{"role": "user", "content": prompt}],
            response_model=JobDescription
        )
    finally:
        client.off("completion:response", count_tokens)
    return result, usage
