import random
import uuid

from ...mail.mail_api import generate_guid

DEVICE_ID = generate_guid()
MPID = str(random.randint(-2**63, -1))
DEVICE_TOKEN = generate_guid()
TRACE_ID = uuid.uuid4().hex
SPAN_ID = uuid.uuid4().hex[:16]

WALLA_BASE_DELAY = 10.0
WALLA_MIN_DELAY = 1.0
WALLA_DELAY_MULTIPLIER = 0.5