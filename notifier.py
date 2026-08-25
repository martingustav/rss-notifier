import json
import tomllib
import sys
import feedparser
import smtplib
from email.message import EmailMessage
import logging
from pathlib import Path
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
        feed = feedparser.parse(feed_url)
    except Exception as e:
        raise FeedError(f"Failed to fetch {feed_url}: {e}") from e

    if feed.bozo:
        raise FeedError(f"Failed to parse {feed_url}: {feed.bozo_exception}")

    channel_name = feed.feed.title
    entries_by_id = dict()
    for entry in feed.entries:
        video_id = entry["yt_videoid"]
        video_title = entry["title"]
        link = entry["link"]
        entries_by_id[video_id] = {"title": video_title, "link": link}
    return channel_name, entries_by_id

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
            channel_name, current_video_ids = fetch_feed(feed_url)
        except FeedError as e:
            logging.warning(e)
            continue

        label = feed_config.get("label") or channel_name

        logging.info(f"Fetched {len(current_video_ids)} from {label}")

        new_video_ids = set()
        if feed_url in state:
            new_video_ids = set(current_video_ids.keys()).difference(set(state[feed_url]))

        if new_video_ids:
            channel_new = dict()
            for video_id in new_video_ids:
                channel_new[video_id] = current_video_ids[video_id]
            all_new[feed_url] = {"label": label, "videos": channel_new}

        state[feed_url] = list(current_video_ids)

    if all_new:
        lines = []
        new_count = 0
        for feed_url, feed_data in all_new.items():
            lines.append(feed_data["label"])
            for video_id, video in feed_data["videos"].items():
                lines.append(f"  {video['title']}")
                lines.append(f"  {video['link']}")
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
