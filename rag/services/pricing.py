from decimal import Decimal


PRICING = {
    "gpt-4o-mini": {"input": Decimal("0.15"), "output": Decimal("0.60")},
    "openai/gpt-4o-mini-2024-07-18": {"input": Decimal("0.20"), "output": Decimal("0.78")},
    "deepseek/deepseek-chat-v3-0324": {"input": Decimal("0.31"), "output": Decimal("1.17")},
    "text-embedding-3-small": {"input": Decimal("0.02"), "output": Decimal("0")},
    "local": {"input": Decimal("0"), "output": Decimal("0")},
}

DEFAULT_PRICE = {"input": Decimal("0"), "output": Decimal("0")}
MILLION = Decimal("1000000")


def calculate_cost(model_name, prompt_tokens=0, completion_tokens=0):
    price = PRICING.get(model_name, DEFAULT_PRICE)
    input_cost = (Decimal(prompt_tokens) / MILLION) * price["input"]
    output_cost = (Decimal(completion_tokens) / MILLION) * price["output"]
    return (input_cost + output_cost).quantize(Decimal("0.00000001"))