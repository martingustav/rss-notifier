This is a simple Python program that fetches entries from RSS feeds
and sends emails with new entries. It is meant to run unattended via
e.g. a cronjob.

Clone this repository and install Python if you don't have it, then
follow the configuration steps below to get started.

# Configuration

## 1. Create the virtual environment

Run this inside the `rss-notifier` directory:

```bash
python -m venv rss-notifier
```

## 2. Install dependencies in the venv

Activate the virtual environment with:

```bash
source rss-notifier/bin/activate
```

Then, inside the virtual environment, run this to install the required
dependencies:

```bash
pip install -r requirements.txt
```

## 3. Enter your email credentials

For this program to be able to send emails, you need to enter your
SMTP credentials in two places:

1. `config.toml`
2. `secrets.toml`

Example files are provided for both.

## 3. Add your RSS feeds

Then, add the feed(s) you want to follow in `config.toml`. An example
file is provided at [config.toml.example](config.toml.example).

To get the correct URL for a YouTube channel's XML feed, you can use
[this
website](https://channelsurfer.tv/tools/youtube-rss-feed/).

Alternatively, use the below manual steps:

1. Go to the YouTube channel you want to have as a feed.
2. Click on the channel description ("...more").
3. Scroll down to the end of the page.
4. Click on "Share channel"
7. Click on "Copy channel ID".
5. Now open a new tab and go to:
   `https://www.youtube.com/feeds/videos.xml?channel_id=<put-channel-ID-here>`

# Running

## To run it once

Inside the venv:

```bash
python notifier.py
```

## Automating it

Add a cronjob:

```bash
crontab -e
```

Example cronjob:

```bash
17 * * * * /path/to/rss-notifier/venv/bin/python3 /path/to/rss-notifier/notifier.py >> /path/to/rss-notifier/cron.log 2>&1
```
