import json
import feedparser

def load_state():
    try:
        with open('state.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error opening state file: file not found.")
        return dict()

def save_state(state):
    with open('state.json', 'w') as f:
        json.dump(state, f, indent=2)
        f.write("\n")

def get_current_ids(feed_url):
    feed = feedparser.parse(feed_url)
    entries_by_id = dict()
    for entry in feed.entries:
        video_id = entry["yt_videoid"]
        title = entry["title"]
        link = entry["link"]
        entries_by_id[video_id] = {"title": title, "link": link}
    return entries_by_id

channel_id = "UCwHwDuNd9lCdA7chyyquDXw"
feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

state = load_state()
current_ids = get_current_ids(feed_url)
new_ids = set()

if channel_id in state:
    new_ids = set(current_ids.keys()).difference(set(state[channel_id]))

state[channel_id] = list(current_ids)
save_state(state)

for video_id in new_ids:
    title = current_ids[video_id].get("title")
    link = current_ids[video_id].get("link")
    print(video_id, title, link)
