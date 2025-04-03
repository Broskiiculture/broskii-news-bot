# broskii_bot.py

import os
import feedparser
import requests
import tweepy
from bs4 import BeautifulSoup

# === API KEYS ===
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_SECRET = os.getenv('X_ACCESS_SECRET')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# === RSS Sources ===
rss_urls = [
    'https://hiphopdx.com/rss',
    'https://www.complex.com/music/rss',
    'https://www.hotnewhiphop.com/rss.xml',
    'https://pitchfork.com/feed-news/rss/',
    'https://www.xxlmag.com/feed/',
    'https://www.rollingstone.com/music/music-news/feed/',
    'https://hypebeast.com/feed',
]

# === Scraping Targets ===
scraping_targets = [
    'https://lyricallemonade.com/',
    'https://www.rollingloud.com/',
    'https://rapradar.com/',
    'https://allhiphop.com/',
    'https://hiphopwired.com/',
]

# === RSS Fetch ===
def fetch_rss():
    news = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append({'title': entry.title, 'link': entry.link})
    return news

# === Scraping ===
def fetch_scraping():
    scraped_news = []
    for url in scraping_targets:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            h2_tags = soup.find_all('h2')
            for tag in h2_tags[:3]:
                link = tag.find('a')['href'] if tag.find('a') else url
                title = tag.get_text(strip=True)
                if title:
                    scraped_news.append({'title': title, 'link': link})
        except Exception as e:
            print(f"[Error scraping] {url}: {e}")
    return scraped_news

# === OpenRouter English Summarize ===
def summarize_en(title, link):
    prompt = f"Summarize the following hiphop news into 3 sentences for SNS:\nTitle: {title}\nURL: {link}"
    data = {"model": "mistralai/mistral-7b-instruct", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    return result['choices'][0]['message']['content'].strip()

# === OpenRouter Japanese Convert ===
def translate_ja(text, link):
    prompt = f"以下の英語ニュース要約を日本語のヒップホップファン向けに分かりやすく、速報感のあるツイート文にしてください。\n{text}\n\n詳細: {link}"
    data = {"model": "mistralai/mistral-7b-instruct", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    return result['choices'][0]['message']['content'].strip()

# === Discord Notify ===
def notify_discord(message):
    payload = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

# === Main ===
def main():
    news = fetch_rss() + fetch_scraping()
    for item in news:
        try:
            en_summary = summarize_en(item['title'], item['link'])
            ja_text = translate_ja(en_summary, item['link'])
            notify_discord(ja_text)
            print(f'✅ 通知成功: {item["title"]}')
        except Exception as e:
            print(f'❌ 通知失敗: {e}')

if __name__ == '__main__':
    main()
