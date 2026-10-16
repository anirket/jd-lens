import os
import time
import instructor
from anthropic import Anthropic
from dotenv import load_dotenv
from job_description import JobDescription
from cost_log import log_run

load_dotenv()

api_key = os.environ['ANTHROPIC_API_KEY']

client = instructor.from_anthropic(Anthropic(api_key=api_key))

model = "claude-haiku-5-5"

# token counter: instructor calls count_tokens() after EVERY API response (retries too)
usage = {"attempts": 0, "input": 0, "output": 0}

def count_tokens(response):
    usage["attempts"] += 1
    usage["input"] += response.usage.input_tokens
    usage["output"] += response.usage.output_tokens

client.on("completion:response", count_tokens)


def extract_job_description(jd_text: str, model: str) -> JobDescription:
    prompt = (
        "Extract the structured details from the job description below.\n\n"
        f"<job_description>\n{jd_text}\n</job_description>"
    )
    return client.messages.create(
        model=model,
        max_tokens=2048,
        max_retries=3,
        messages=[{"role": "user", "content": prompt}],
        response_model=JobDescription
    )


if __name__ == "__main__":
    # sample JD to test 1 extraction
    with open("JD/sarvam_frontend_engineer_chanakya.txt", "r") as f:
        job_description = f.read()

    start = time.time()
    job_extraction = extract_job_description(job_description, model)
    seconds = time.time() - start

    print(job_extraction.model_dump_json(indent=2))

    log_run(model, "sarvam_frontend", usage["attempts"], usage["input"], usage["output"], seconds)
