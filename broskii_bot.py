# broskii_bot.py

import os
import feedparser
import requests
import sqlite3
from bs4 import BeautifulSoup

# === API Keys ===
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
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

# === News Fetch ===
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
            print(f"⚠️ [SCRAPE ERROR] {url}: {e}")
    return news

# === Duplication Check ===
def is_posted(url):
    cursor.execute('SELECT 1 FROM posts WHERE url = ?', (url,))
    return cursor.fetchone() is not None

def mark_posted(url):
    cursor.execute('INSERT OR IGNORE INTO posts (url) VALUES (?)', (url,))
    conn.commit()

# === Translate ===
def translate_to_ja(title, link):
    prompt = f"""
以下の海外ヒップホップニュースを、日本のヘッズ向けに速報っぽく翻訳しろ。

- シンプルで速く読める
- SNS映え & 拡散されやすく
- キャラ: USヒップホップオタク70% + 速報メディア30%
- シーン、ビーフ、ドリル、リリック、クルーなどの語彙は積極使用
- 無理な翻訳不要、自然にオタクが喋ってる感じ
- 文末に「詳細: {link}」を必ずつける

【ニュース原文】
{title}
    """

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "openrouter/openai/gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    try:
        result = res.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ API Error: {e}, content: {res.text}")
        return None

# === Discord Notify ===
def post_to_discord(text, link):
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        og = soup.find('meta', property='og:image')
        image_url = og['content'] if og else None
    except Exception as e:
        print(f"⚠️ OGP取得失敗: {e}")
        image_url = None

    embed = {"title": "🟣 Broskii News", "description": text, "url": link}
    if image_url:
        embed["image"] = {"url": image_url}

    payload = {"embeds": [embed]}
    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if res.status_code != 204:
        raise Exception(f"Discord Webhook failed: {res.text}")

# === MAIN ===
def main():
    news = fetch_rss() + fetch_scraping()
    for item in news:
        if is_posted(item['link']):
            print(f'⏩ skip: {item["title"]}')
            continue
        try:
            ja_text = translate_to_ja(item['title'], item['link'])
            if ja_text:
                post_to_discord(ja_text, item['link'])
                mark_posted(item['link'])
                print(f'✅ posted: {item["title"]}')
        except Exception as e:
            print(f'❌ Error: {e}')

if __name__ == '__main__':
    main()
