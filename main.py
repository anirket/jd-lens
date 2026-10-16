import os
import instructor
from anthropic import Anthropic
from dotenv import load_dotenv
from job_description import JobDescription

load_dotenv()

api_key = os.environ['ANTHROPIC_API_KEY']

client = instructor.from_anthropic(Anthropic(api_key=api_key))

model = "claude-haiku-5-5"

# sample JD to test 1 extraction
with open("JD/sarvam_frontend_engineer_chanakya.txt", "r") as f:
    job_description = f.read()

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
    job_extraction = extract_job_description(job_description, model)
    print(job_extraction.model_dump_json(indent=2))


