from pathlib import Path
from openai import OpenAI

env_file = Path("C:/Users/aman/Documents/meta/horizonforge-local-test/.env")
for line in env_file.read_text(encoding="utf-8").splitlines():
    if line.startswith("MODEL_API_KEY="):
        api_key = line.split("=", 1)[1].strip()

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=api_key)
resp = client.chat.completions.create(
    model="muse-spark-1.3",
    reasoning_effort="minimal",
    max_completion_tokens=4096,
    temperature=0.2,
    messages=[{"role": "user", "content": 'Return JSON: {"msg": "ok"}'}]
)
print('Content:', resp.choices[0].message.content)
print('Finish reason:', resp.choices[0].finish_reason)
print('Usage:', resp.usage)
