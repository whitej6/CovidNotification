# Covid Notification

## Simple Slack + Docker Python API Scraper
Scrapes an API endpoint exposed by H-E-B and based on `config.yml` will send notifications to a slack channel

### Example config.yml
```yaml
---
# To get your token just go to https://api.slack.com/custom-integrations/legacy-tokens Scroll down to the "Legacy information" section and click Issue token/Re-issue token
token: "xoxp-XXX-XXX-XXX-XXXXX"

# To obtain the Channel ID, Right-Click on the channel, or direct message and click copy link. The id is the last part of that link
# e.g. https://your_org.slack.com/archives/YOUR_CHANNEL_ID
channel: "XXXXXX"

# H-E-B Information
url: "https://heb-ecom-covid-vaccine.hebdigital-prd.com/vaccine_locations.json"
# Replace with icon you would like to show up in Slack
icon: ":XXXXX:"
# Replace with zip codes for the Locations you would like to be notified of
zip_codes:
  - "77055"
  - "77302"
  - "77386"
```

### Build & Launch command for Docker
```bash
docker build -t covid_bot:latest .
docker run -itd --name covid_bot covid_bot:latest
```