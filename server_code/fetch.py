import anvil.secrets
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

from .s3i import broker

broker = broker.Broker()


@anvil.server.background_task
def fetch_s3i():
  pass
