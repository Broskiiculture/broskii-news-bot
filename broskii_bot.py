# broskii_bot.py

import os
import feedparser
import requests
import sqlite3
from bs4 import BeautifulSoup
import sqlite3

# === API Keys ===
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# === DB setup for duplication check ===
conn = sqlite3.connect('posted.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS posts (url TEXT PRIMARY KEY)')
conn.commit()

# === Sources ===
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

# === Get RSS News ===
def fetch_rss():
    news = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append({'title': entry.title, 'link': entry.link})
    return news

# === Scrape HTML News ===
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

# === Translate with OpenRouter (オタク x ライター) ===
def translate_to_ja(title, link):
    prompt = f"""
あなたはUSヒップホップのオタクであり、速報メディアのライターでもあります。
以下の英語ニュースを、日本のヒップホップファン向けに速報ツイート風に翻訳してください。

指示:
- ヒップホップシーンっぽさ、オタクっぽさを出す（語彙例: シーン、ビーフ、ドリル、リリック、クルー、ムーブメント、バイブス）
- 速報性を意識した文体（「速報」や「ついに」など）
- 文末は「！」か「。」で統一
- 日本語として自然で、読みやすく
- 絵文字は不要
- 必ず最後に「詳細: {link}」を追記

【元ニュース】
{title}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openhermes-2.5-mistral",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400
    }

    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = res.json()
    return result['choices'][0]['message']['content'].strip()


# === Discord Notify ===
def post_to_discord(text):
    data = {"content": text}
    r = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if r.status_code != 204:
        raise Exception(f"Discord Webhook failed: {r.text}")

# === Duplication check ===
def is_duplicate(url):
    cursor.execute('SELECT 1 FROM posts WHERE url = ?', (url,))
    return cursor.fetchone() is not None

def mark_posted(url):
    cursor.execute('INSERT OR IGNORE INTO posts (url) VALUES (?)', (url,))
    conn.commit()

# === 重複チェック用DB ===
conn = sqlite3.connect("posted.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posts (title TEXT, link TEXT)")
conn.commit()

def is_posted(title, link):
    cur.execute("SELECT * FROM posts WHERE title=? OR link=?", (title, link))
    return cur.fetchone() is not None

def save_post(title, link):
    cur.execute("INSERT INTO posts (title, link) VALUES (?, ?)", (title, link))
    conn.commit()


# === Main ===
def main():
    init_db()
    news = fetch_rss() + fetch_scraping()
    for item in news:
    if is_posted(item['title'], item['link']):
        print(f'⏭️ スキップ: {item["title"]}')
        continue
    try:
        ja_text = translate_to_ja(item['title'], item['link'])
        post_to_discord(ja_text)
        save_post(item['title'], item['link'])
        print(f'✅ 通知成功: {item["title"]}')
    except Exception as e:
        print(f'❌ 通知失敗: {e}')


if __name__ == '__main__':
    main()
