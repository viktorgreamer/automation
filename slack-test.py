import logging

# logging.basicConfig(level=logging.DEBUG)

import os
from slack_sdk import WebClient

client = WebClient(token='a43e4c80b02accdc24de468e0c35cbb0')

response = client.chat_postMessage(
    channel="general",
    text="Hello from your app! :tada:"
)
