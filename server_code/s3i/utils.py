import uuid


def generate_message_identifier() -> str:
    """Generate a unique message identifier."""
    return f"s3i:{str(uuid.uuid4())}"
