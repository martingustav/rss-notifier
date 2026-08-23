import json
import tomllib
import sys
import feedparser

def load_state():
    try:
        with open('state.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Normal on first run; start with empty state
        return dict()
    except json.JSONDecodeError:
        # Abnormal; fail loudly rather than silently resetting
        print("state.json is corrupt or empty. Delete it to start fresh.")
        sys.exit(1)

def load_config():
    try:
        with open('config.toml', 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        print("Error opening config file: file not found.")
        sys.exit(1)

def save_state(state):
    with open('state.json', 'w') as f:
        json.dump(state, f, indent=2)
        f.write("\n")

def fetch_feed(feed_url):
    feed = feedparser.parse(feed_url)
    channel_name = feed.feed.title
    entries_by_id = dict()
    for entry in feed.entries:
        video_id = entry["yt_videoid"]
        video_title = entry["title"]
        link = entry["link"]
        entries_by_id[video_id] = {"title": video_title, "link": link}
    return channel_name, entries_by_id

state = load_state()
config = load_config()
all_new = dict()

for feed_config in config["feeds"]:
    feed_url = feed_config["url"]
    channel_name, current_video_ids = fetch_feed(feed_url)
    label = feed_config.get("label") or channel_name
    new_video_ids = set()

    if feed_url in state:
        new_video_ids = set(current_video_ids.keys()).difference(set(state[feed_url]))

    if new_video_ids:
        channel_new = dict()
        for video_id in new_video_ids:
            channel_new[video_id] = current_video_ids[video_id]
        all_new[feed_url] = {"label": label, "videos": channel_new}

    state[feed_url] = list(current_video_ids)

save_state(state)

for feed_url, feed_data in all_new.items():
    for video_id, video in feed_data["videos"].items():
        print(feed_data["label"], video["title"], video["link"])
