import anvil.secrets
import httpx

from .s3i import broker

client = httpx.AsyncClient()
self_thing = broker.Thing(
    id=anvil.secrets.get_secret("s3i_id"),
    secret=anvil.secrets.get_secret("s3i_secret"),
    message_queue=anvil.secrets.get_secret("s3i_message_queue"),
    event_queue=anvil.secrets.get_secret("s3i_event_queue"),
)
broker = broker.Broker(self_thing, client=client)


@anvil.server.background_task
def fetch_s3i():
    """Fetch messages from the S3I message broker a single time and do the appropriate tasks."""
    # TODO: Implement this function.
