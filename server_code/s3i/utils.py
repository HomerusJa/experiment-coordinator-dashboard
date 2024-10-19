import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server

import uuid

def generate_message_identifier() -> str:
    """Generate a unique message identifier."""
    return f"s3i:{str(uuid.uuid4())}"
  