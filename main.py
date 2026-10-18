import os
import time
import instructor
from anthropic import Anthropic
from dotenv import load_dotenv
from job_description import JobDescription
from cost_log import log_run
from pathlib import Path

load_dotenv()

api_key = os.environ['ANTHROPIC_API_KEY']

# JSON mode: newer models (e.g. Opus 5.5) reject the forced tool call that the default TOOLS mode uses
client = instructor.from_anthropic(Anthropic(api_key=api_key), mode=instructor.Mode.ANTHROPIC_JSON)

model = "claude-haiku-5-5"

def extract_job_description(jd_text: str, model: str) -> JobDescription:
    # token counter: instructor calls count_tokens() after EVERY API response (retries too)
    usage = {"attempts": 0, "input": 0, "output": 0}

    def count_tokens(response):
        usage["attempts"] += 1
        usage["input"] += response.usage.input_tokens
        usage["output"] += response.usage.output_tokens

    client.on("completion:response", count_tokens)

    prompt = (
        "Extract the structured details from the job description below.\n\n"
        f"<job_description>\n{jd_text}\n</job_description>"
    )
    try:
        result = client.messages.create(
            model=model,
            max_tokens=2048,
            max_retries=3,
            messages=[{"role": "user", "content": prompt}],
            response_model=JobDescription
        )
    finally:
        client.off("completion:response", count_tokens)
    return result, usage


if __name__ == "__main__":
    for case in sorted(Path("evals/cases").glob("*.txt")):
        start = time.time()
        job_extraction, usage = extract_job_description(case.read_text(), model)
        seconds = time.time() - start

        print(job_extraction.model_dump_json(indent=2))

        log_run(model, case.stem, usage["attempts"], usage["input"], usage["output"], seconds)
