import json
import uuid


def print_step(title, data):
    print(f"\n--- {title} ---")
    print(json.dumps(data, indent=2))

def generate_request_id(last_digit='1'):
    """Generates a random UUID, allowing the last digit to be controlled for mock status."""
    base_uuid = str(uuid.uuid4())
    return base_uuid[:-1] + last_digit