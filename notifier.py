import json
import tomllib
import sys
import feedparser
import smtplib
from email.message import EmailMessage
import logging
from pathlib import Path
from xml.sax import SAXParseException
import requests
BASE_DIR = Path(__file__).resolve().parent

class FeedError(Exception):
    pass

def load_state():
    try:
        with open(BASE_DIR / 'state.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Normal on first run; start with empty state
        return dict()
    except json.JSONDecodeError:
        # Abnormal; fail loudly rather than silently resetting
        logging.error("state.json is corrupt or empty. Delete it to start fresh.")
        sys.exit(1)

def load_config():
    try:
        with open(BASE_DIR / 'config.toml', 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        logging.error("Error opening config file: file not found.")
        sys.exit(1)

def load_secrets():
    try:
        with open(BASE_DIR / 'secrets.toml', 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        logging.error("Error opening secrets file: file not found.")
        sys.exit(1)

def save_state(state):
    with open(BASE_DIR / 'state.json', 'w') as f:
        json.dump(state, f, indent=2)
        f.write("\n")

def fetch_feed(feed_url):
    try:
        response = requests.get(feed_url, timeout=15)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

    except Exception as e:
        raise FeedError(f"Failed to fetch {feed_url}: {e}") from e

    if feed.bozo:
        raise FeedError(f"Failed to parse {feed_url}: {feed.bozo_exception}")

    feed_title = feed.feed.title
    entries_by_link = dict()
    for entry in feed.entries:
        title = entry["title"]
        link = entry["link"]
        entries_by_link[link] = {"title": title}
    return feed_title, entries_by_link

def send_email(subject, body, config, password):
    host = config["email"]["smtp_host"]
    port = config["email"]["smtp_port"]
    username = config["email"]["smtp_username"]
    from_address = config["email"]["from_address"]
    to_address = config["email"]["to_address"]

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address

    with smtplib.SMTP_SSL(host, port) as s:
        s.login(username, password)
        s.send_message(msg)

    logging.info(f"Email sent to {to_address} from {from_address}")

def main():
    logging.basicConfig(
        filename=BASE_DIR / "rss_notifier.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    logging.info("Started")

    state = load_state()
    config = load_config()
    password = load_secrets()["smtp_password"]
    all_new = dict()

    # Get new feed entries
    for feed_config in config["feeds"]:
        feed_url = feed_config["url"]
        try:
            feed_title, current_entries = fetch_feed(feed_url)
        except FeedError as e:
            logging.warning(e)
            continue

        label = feed_config.get("label") or feed_title

        logging.info(f"Fetched {len(current_entries)} from {label}")

        new_entries = set()
        if feed_url in state:
            new_entries = set(current_entries.keys()).difference(set(state[feed_url]))

        if new_entries:
            feed_new = dict()
            for link in new_entries:
                feed_new[link] = current_entries[link]
            all_new[feed_url] = {"label": label, "entries": feed_new}

        state[feed_url] = list(current_entries)

    if all_new:
        lines = []
        new_count = 0
        for feed_url, feed_data in all_new.items():
            lines.append(feed_data["label"])
            for link, entry in feed_data["entries"].items():
                lines.append(f"  {entry['title']}")
                lines.append(f"  {link}")
                lines.append("")
                new_count += 1
        body = "\n".join(lines)
        subject = ""

        if new_count > 1:
            subject = f"{new_count} new feed entries"
        else:
            subject = f"{new_count} new feed entry"

        logging.info(subject)

        send_email(subject, body, config, password)
    else:
        logging.info("No new feed entries.")

    # Save state after sending email
    # so state gets discarded if email
    # fails
    save_state(state)

    logging.info("Finished")

if __name__ == "__main__":
    main()
