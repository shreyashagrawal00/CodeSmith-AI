import json
import re


def extract_json(text: str) -> dict:
    """Extract a JSON object from a string, handling markdown code blocks."""
    # Try to find JSON in markdown code block
    match = re.search(r"```(?:json)?\n?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1)

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Could not parse JSON from text: {text[:200]}...")
