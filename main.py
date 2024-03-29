import os
import requests
import time
import zulip
import re
import feedparser
import markdownify
from datetime import datetime, timedelta, timezone

# Define your Zulip credentials
ZULIP_EMAIL = os.environ.get('ZULIP_EMAIL')
ZULIP_STREAM_NAME = 'articles'

# Define the dictionary of feed names and their RSS links
RSS_FEEDS = {
    "Dan Ma's Topology Blog" : "https://dantopology.wordpress.com/feed/"
    "The Higher Geometer" : "https://thehighergeometer.wordpress.com/feed/"
    "Terence Tao" : "https://terrytao.wordpress.com/feed/"
    "Mathematics, Quanta Magazine" : "https://api.quantamagazine.org/mathematics/feed"
    "Physics, Quanta Magazine" : "https://api.quantamagazine.org/physics/feed"
    "Biology, Quanta Magazine" : "https://api.quantamagazine.org/biology/feed"
    "Computer Science, Quanta Magazine" : "https://api.quantamagazine.org/computer-science/feed"
}

# Function to send a message to Zulip
def send_zulip_message(content, topic):
    client = zulip.Client(email=ZULIP_EMAIL, client='rss-feed-bot/0.1')
    data = {
        "type": "stream",
        "to": ZULIP_STREAM_NAME,
        "topic": topic,
        "content": content,
    }
    client.send_message(data)

# Get the url of the last article update sent to the stream
def last_article_update_link(topic):
    client = zulip.Client(email=ZULIP_EMAIL, client='test-github-client/0.1')
    request: Dict[str, Any] = {
        "anchor": "newest",
        "num_before": 1,
        "num_after": 0,
        "narrow": [
            {"operator": "sender", "operand": ZULIP_EMAIL},
            {"operator": "stream", "operand": ZULIP_STREAM_NAME},
            {"operator": "topic", "operand": topic},
        ],
        "apply_markdown": False
    }
    response = client.get_messages(request)
    if response['result'] == "success":
        messages = response["messages"]
        if messages:
            latest_message = messages[0]
            latest_message_content = latest_message["content"]
            url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
            latest_arxiv_link = re.findall(url_pattern, latest_message_content)[0]
            return latest_arxiv_link
        else:
            return None
    else:
        print(f"Failed to retrieve message or No previous messages")
        return None

# Function to fetch latest articles from arXiv
def update_zulip_stream():
    for  feed_name, feed_url in RSS_FEEDS.items():
        feed = feedparser.parse(feed_url)
        topic = feed.feed.title
        last_updated_article_link = last_article_update_link(topic)
        flag = True if last_updated_article_link else False # To avoid the case when not having an article ends up not getting to the execution part of the for loop
        for article in feed.entries[:4][::-1]: #This is to get the latest 5 articles in ascending order by time
            link = article.link
            if flag:
                if link == last_updated_article_link:
                    flag = False
                continue
            title = markdownify.markdownify(article.title.replace('$^{\\ast}$', '* ').replace('$^*$', '* ').replace('$^*$', '* ').replace("$", "$$").replace("\n", " "))
            published = time.strftime("%d %B %Y", article.published_parsed)
            author = article.author
            summary = markdownify.markdownify(article.description)
            tags = ", ".join([entry['term'] for entry in article.tags])
            message = f"\n**[{title}]({link})**\n*{author}, {published}*\n\n{summary}\n\n*{tags}*"
            # send_zulip_message(message, topic)
            print(message)

# Main function to check for new articles periodically
if __name__ == "__main__":
    update_zulip_stream()
