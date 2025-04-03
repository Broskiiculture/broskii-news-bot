# broskii_bot.py (DeepSeek R1 対応版)

import os
import feedparser
import requests
import sqlite3
from bs4 import BeautifulSoup

# === API Keys ===
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# === DB ===
conn = sqlite3.connect('posted.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS posts (url TEXT PRIMARY KEY)')
conn.commit()

# === RSS & Scraping Targets ===
rss_urls = [
    'https://hiphopdx.com/rss',
    'https://www.complex.com/music/rss',
    'https://pitchfork.com/feed-news/rss/',
    'https://www.xxlmag.com/feed/',
    'https://www.rollingstone.com/music/music-news/feed/',
    'https://hypebeast.com/feed',
]

scraping_targets = [
    'https://lyricallemonade.com/',
    'https://www.rollingloud.com/',
    'https://rapradar.com/',
    'https://allhiphop.com/',
    'https://hiphopwired.com/',
]

# === Fetch ===
def fetch_rss():
    news = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append({'title': entry.title, 'link': entry.link})
    return news


def fetch_scraping():
    news = []
    for url in scraping_targets:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for h2 in soup.find_all('h2')[:3]:
                link = h2.find('a')['href'] if h2.find('a') else url
                title = h2.get_text(strip=True)
                if title:
                    news.append({'title': title, 'link': link})
        except Exception as e:
            print(f"[SCRAPE ERROR] {url}: {e}")
    return news

# === Duplication Check ===
def is_posted(link):
    cursor.execute('SELECT 1 FROM posts WHERE url = ?', (link,))
    return cursor.fetchone() is not None


def save_post(link):
    cursor.execute('INSERT OR IGNORE INTO posts (url) VALUES (?)', (link,))
    conn.commit()

# === DeepSeek Translator ===
def translate_to_ja(title, link):
    prompt = f"""
以下の海外ヒップホップニュースを、日本のヘッズ向けに速報ツイート文にしてください。

- 内容は端的、かつ拡散されやすく
- スラング＆専門用語は自然に活用 (シーン, ビーフ, クルー, リリック, ドリル等)
- US HipHopオタク70% × 速報ライター30% の語り口
- 最後に「詳細: {link}」

[News]
{title}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
    "model": "deepseek-ai/deepseek-chat",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 300
}

    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    try:
        result = res.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ API応答エラー: {e}, content: {res.text}")
        return None

# === Discord Notify ===
def post_to_discord(text, link):
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        image_url = og_image['content'] if og_image else None
    except Exception as e:
        print(f"⚠️ OGP取得失敗: {e}")
        image_url = None

    embed = {
        "title": "🟣 Broskii News",
        "description": text,
        "url": link
    }
    if image_url:
        embed["image"] = {"url": image_url}

    payload = {"embeds": [embed]}
    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if res.status_code != 204:
        raise Exception(f"Discord Webhook failed: {res.text}")

# === Main ===
def main():
    news = fetch_rss() + fetch_scraping()
    for item in news:
        if is_posted(item['link']):
            print(f'⏭️ skip: {item["title"]}')
            continue
        ja_text = translate_to_ja(item['title'], item['link'])
        if ja_text:
            post_to_discord(ja_text, item['link'])
            save_post(item['link'])
            print(f'✅ posted: {item["title"]}')

if __name__ == "__main__":
    main()
