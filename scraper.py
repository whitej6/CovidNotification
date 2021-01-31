import requests
import yaml
import slack
import time
import logging
import os

with open('config.yml', 'r') as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)

URL = CONFIG['url']
ZIP_CODES = CONFIG['zip_codes']
TOKEN = CONFIG['token']
CHANNEL = CONFIG['channel']
ICON = CONFIG['icon']
APPTS_FOUND = {}

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger('covid_appt_bot')

def post_to_slack(message, city):
    client = slack.WebClient(token=TOKEN)
    client.chat_postMessage(
        channel=CHANNEL,
        blocks=message,
        as_user=False,
        username=city,
        icon_emoji=ICON
    )

def format_block(payload):
    response = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<!here> An appointment was located at your local *H-E-B*!"
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Type*"
                },
                {
                    "type": "plain_text",
                    "text": payload['type']
                },
                {
                    "type": "mrkdwn",
                    "text": "*Location*"
                },
                {
                    "type": "plain_text",
                    "text": payload['name']
                },
                {
                    "type": "mrkdwn",
                    "text": "*Available Time Slots*"
                },
                {
                    "type": "plain_text",
                    "text": str(payload['openTimeslots'])
                },
                {
                    "type": "mrkdwn",
                    "text": "*Available Appointment Slots*"
                },
                {
                    "type": "plain_text",
                    "text": str(payload['openAppointmentSlots'])
                },
                {
                    "type": "mrkdwn",
                    "text": "*Address*"
                },
                {
                    "type": "plain_text",
                    "text": f"{payload['street']}\n{payload['city']},{payload['state']} {payload['zip']}"
                }
            ]
        }
    ]
    return response

while True:
    log.info("Querying API")
    r = requests.get(URL)
    json = r.json()
    for i in json.get('locations', []):
        if i['zip'][:5] in ZIP_CODES:
            if i['openAppointmentSlots'] or i['openTimeslots']:
                log.info(f'Appointment found at {i["name"]}')
                if not APPTS_FOUND.get(i['name'], False):
                    log.info('Sending message to slack')
                    post_to_slack(format_block(i), i.get('city'))
                    APPTS_FOUND[i['name']] = True
                else:
                    log.info('Message previously sent to slack')
            else:
                log.debug('No appointments found.')
                APPTS_FOUND[i['name']] = False
    time.sleep(10)
