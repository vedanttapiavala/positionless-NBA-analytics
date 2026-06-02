import requests
from bs4 import BeautifulSoup
from collections import deque
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
import re

# Description of the code:
# This code relies on seeding potential inputs to the injury database search queries, such as "ankle"
# It searches all seeds in the database and uses the search results to flag new potential terms.
# The code also opens a new window, where you can see the size of your search queue and injury list output items
# You can also see the current query on that window.

def get_field(name):
    return soup.find("input", {"name": name})["value"]

# Step 2: POST with search term
def search(query):
    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": vsgenerator,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00$ContentPlaceHolder1$Table1": query,
        "ctl00$ContentPlaceHolder1$Button1": "Search",
        # UpdatePanel async fields
        "ctl00$ScriptManager1": "ctl00$UpdatePanel1|ctl00$ContentPlaceHolder1$Button1",
        "ScriptManager1_HiddenField": "",
    }
    headers = {
        "X-MicrosoftAjax": "Delta=true",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": BASE,
    }
    r = session.post(BASE, data=payload, headers=headers)
    
    # Response is pipe-delimited; extract the HTML chunk
    # The table HTML is inside the updatePanel block
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", {"id": "ContentPlaceHolder1_GridView2"})
    
    urls = []
    if table is None:
        return []
    for row in table.find_all("tr")[1:]:  # skip header
        a = row.find("a")
        if a and a.get("href"):
            urls.append(a["href"])
    return urls

def scraper_thread():
    queries = ['illness', 'nba', 'health', 'safety', 'protocol',
            'sprained', 'left', 'ankle', 'right', 'sore', 'knee',
            'injury', 'back', 'concussion', 'covid-19']
    queries = deque(queries)
    seen = set()
    url_suffixes = set()
    banned_queries = ['in', 'of', '/', 'the', 'a', 'an',
                    'to', 'on', 'and', 'or', 'from', 'y']
    counter = 0
    while queries:
        q = queries.popleft()
        with lock:
            state['current_word'] = q
        if q in seen:
            continue
        seen.add(q)
        urls = search(q)
        new_urls = [u for u in urls if u not in url_suffixes]
        url_suffixes.update(urls)
        with open("data/injury_url_suffixes.txt", "a") as f:
            for u in new_urls:
                f.write(u + "\n")
        time.sleep(0.5)

        for u in urls:
            term = u.lower().replace('/injury/','')
            term_split = term.split('-')
            for t in term_split:
                t = re.sub(r'[^a-z0-9]', '', t)
                if not t:
                    continue
                if t in banned_queries:
                    continue
                if t not in queries and t not in seen:
                    queries.append(t)
        counter+=1
        with lock:
            state['counter'] = counter
            state['queue_size'] = len(queries)
            state['url_count'] = len(url_suffixes)
            history['count'].append(counter)
            history['queue_size'].append(len(queries))
            history['urls'].append(len(url_suffixes))
    with lock:
        state['done'] = True

def animate(_):
    with lock:
        x    = list(history["count"])
        q    = list(history["queue_size"])
        u    = list(history["urls"])
        word = state["current_word"]
        cnt  = state["counter"]
        done = state["done"]

    ax1.cla()
    ax2.cla()

    for ax in (ax1, ax2):
        ax.set_facecolor("#1a1a1a")
        ax.tick_params(colors="gray", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")

    ax1.set_title("Queue size", color="#aaa", fontsize=9)
    ax1.set_xlabel("queries processed", color="#aaa", fontsize=8)
    ax2.set_title("Unique URLs found", color="#aaa", fontsize=9)
    ax2.set_xlabel("queries processed", color="#aaa", fontsize=8)

    if x:
        ax1.plot(x, q, color="#4a9eff", linewidth=1.5)
        ax1.fill_between(x, q, alpha=0.15, color="#4a9eff")
        ax2.plot(x, u, color="#44ff88", linewidth=1.5)
        ax2.fill_between(x, u, alpha=0.15, color="#44ff88")

    status = f"● {word}" if not done else "✓ done"
    word_text.set_text(status)
    counter_text.set_text(f"{cnt} processed  |  {u[-1] if u else 0} URLs")

BASE = "https://hashtagbasketball.com/nba-injury"

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Step 1: GET to grab hidden fields
r = session.get(BASE)
soup = BeautifulSoup(r.text, "html.parser")

viewstate     = get_field("__VIEWSTATE")
vsgenerator   = get_field("__VIEWSTATEGENERATOR")
eventvalidation = get_field("__EVENTVALIDATION")

lock = threading.Lock()
state = {
    'counter': 0,
    'queue_size': 0,
    'url_count': 0,
    'current_word': 'starting...',
    'done': False
}
history = {
    'count': [],
    'queue_size': [],
    'urls': [],
}

fig = plt.figure(figsize=(11, 5), facecolor="#0f0f0f")
fig.suptitle("NBA Injury Crawler", color="white", fontsize=13, fontweight="bold", y=0.97)
gs = GridSpec(1, 2, figure=fig, wspace=0.35)

ax1 = fig.add_subplot(gs[0])  # queue size
ax2 = fig.add_subplot(gs[1])  # urls found

for ax in (ax1, ax2):
    ax.set_facecolor("#1a1a1a")
    ax.tick_params(colors="gray", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")

ax1.set_title("Queue size", color="#aaa", fontsize=9)
ax1.set_xlabel("queries processed", color="#aaa", fontsize=8)
ax2.set_title("Unique URLs found", color="#aaa", fontsize=9)
ax2.set_xlabel("queries processed", color="#aaa", fontsize=8)

# Current word text in top-right of figure
word_text = fig.text(0.98, 0.95, "", ha="right", va="top",
                     fontsize=10, color="#44ff88",
                     fontfamily="monospace",
                     bbox=dict(boxstyle="round,pad=0.3", fc="#1a1a1a", ec="#333"))

counter_text = fig.text(0.98, 0.83, "", ha="right", va="top",
                        fontsize=8, color="#888")

ani = animation.FuncAnimation(fig, animate, interval=800, cache_frame_data=False)

thread = threading.Thread(target=scraper_thread, daemon=True)
thread.start()

plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.show()