import logging
import os
import time
from typing import Any, Dict, List
import yaml

import requests
import slack

with open("config.yml", "r") as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)

URL = CONFIG["url"]
ZIP_CODES = CONFIG["zip_codes"]
TOKEN = CONFIG["token"]
CHANNEL = CONFIG["channel"]
ICON = CONFIG["icon"]
THRESHOLD = CONFIG["threshold"]
APPTS_FOUND = {}
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")

logging.basicConfig(
    level=LOGLEVEL,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("covid_appt_bot")
log.setLevel(LOGLEVEL)  # Required to make below conditional slack messaging work


def post_to_slack(message: List[Dict[str, Any]], city: str):
    client = slack.WebClient(token=TOKEN)
    client.chat_postMessage(
        channel=CHANNEL,
        blocks=message,
        # as_user=False,  # Throws SlackApiError, Deprecated
        username=city,
        icon_emoji=ICON,
    )


def format_block(payload: Dict[str, str], success: bool) -> List[Dict[str, Any]]:
    """
    Given the response payload for a location, format it for slack.

    If there was no success, format a failure message.
    """

    if success:
        response = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<!here> An appointment was located at your local *H-E-B*! https://vaccine.heb.com/scheduler?q=" + payload['zip'],
                },
                "fields": [
                    {"type": "mrkdwn", "text": "*Type*"},
                    {"type": "plain_text", "text": payload["type"]},
                    {"type": "mrkdwn", "text": "*Location*"},
                    {"type": "plain_text", "text": payload["name"]},
                    {"type": "mrkdwn", "text": "*Available Time Slots*"},
                    {"type": "plain_text", "text": str(payload["openTimeslots"])},
                    {"type": "mrkdwn", "text": "*Available Appointment Slots*"},
                    {
                        "type": "plain_text",
                        "text": str(payload["openAppointmentSlots"]),
                    },
                    {"type": "mrkdwn", "text": "*Address*"},
                    {
                        "type": "plain_text",
                        "text": f"{payload['street']}\n{payload['city']}, {payload['state']} {payload['zip']}",
                    },
                ],
            }
        ]
    else:
        response = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "An appointment was NOT located at any of your local *H-E-B* locations...",
                },
            }
        ]
    return response


# Sends a startup message so you know it's working correctly.
message = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Bot has started monitoring zip codes {', '.join(ZIP_CODES)}",
            },
        }
    ]
post_to_slack(message, "Bot")

while True:

    # Figure out if we found _any_ appointments
    any_appts_found = False

    log.info("Querying API for %s ZIP codes", str(len(ZIP_CODES)))
    r = requests.get(URL)
    json = r.json()
    for i in json.get("locations", []):
        if i["zip"][:5] in ZIP_CODES:
            # We didn't find any Timeslots or appointments in those timeslots
            if not i["openTimeslots"] and not i["openAppointmentSlots"]:
                log.debug("No appointments found.")
                APPTS_FOUND[i["name"]] = False

            # We found some open appointment slots, however they were below the set threshold
            elif (
                i["openAppointmentSlots"] < THRESHOLD and i["openAppointmentSlots"] > 0
            ):
                log.info(
                    "%s slot(s) found at %s, below threshold of %s",
                    str(i["openAppointmentSlots"]),
                    i.get("name"),
                    str(THRESHOLD),
                )
                APPTS_FOUND[i["name"]] = False

            # So therefore if we're here, we must have something to show for it
            else:
                log.info(
                    "%s appointment(s) found at %s",
                    str(i["openAppointmentSlots"]),
                    i["name"],
                )
                if not APPTS_FOUND.get(i["name"], False):
                    log.info("Sending message to slack")
                    post_to_slack(format_block(i, True), i.get("city"))
                    APPTS_FOUND[i["name"]] = True
                    any_appts_found = True
                else:
                    log.info("Message previously sent to slack")

    if log.level == 10 and not any_appts_found:
        post_to_slack(format_block(i, False), i.get("city"))
    time.sleep(10)
