from openai import OpenAI

client = OpenAI(
    api_key="cap-5c97e38ed73d3622ec2f12f8c261933e",
    base_url="https://cloudapi.uz/api/v1"
)

r = client.chat.completions.create(
    model="openai/gpt-oss-120b:free",
    messages=[{"role": "user", "content": "Salom! O'zbek tilida javob ber: 2+2 nechchi?"}]
)
print(r.choices[0].message.content)
print("Usage:", r.usage)