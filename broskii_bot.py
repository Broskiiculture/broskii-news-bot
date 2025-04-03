# broskii_bot.py

import os
import feedparser
import requests
import sqlite3
from bs4 import BeautifulSoup

# === API Keys ===
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# === DB setup for duplication check ===
conn = sqlite3.connect('posted.db')
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS posts (title TEXT, link TEXT)")
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

# === Translate with OpenRouter (openhermes) ===
def translate_to_ja(title, link):
    prompt = f"""
以下は海外のヒップホップニュースです。  
これを日本語のヒップホップファン向けに、X（旧Twitter）に投稿する速報ツイートとして仕上げてください。

制約:
- シンプル、短く、バズりやすく
- USヒップホップオタクが日本語で投稿するような口調
- シーン、リリック、ビーフ、ドリル、クルーなどシーン用語を必要なら自然に使う
- ファンの興奮やリアクションも少し混ぜてOK
- 和訳じゃなく、ニュースを日本語のHipHopクラスタ向けに最適化
- 最後に「詳細: {link}」を必ず記載
- 不要なら記事の元URL内の英語タイトルは使わなくてOK

元ネタ:
{title}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openhermes",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300
    }

    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = res.json()
    return result['choices'][0]['message']['content'].strip()


# === Discord Notify with OGP ===
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

# === Duplication Check ===
def is_posted(title, link):
    cur.execute("SELECT * FROM posts WHERE title=? OR link=?", (title, link))
    return cur.fetchone() is not None

def save_post(title, link):
    cur.execute("INSERT INTO posts (title, link) VALUES (?, ?)", (title, link))
    conn.commit()

# === Main ===
def main():
    news = fetch_rss() + fetch_scraping()
    for item in news:
        if is_posted(item['title'], item['link']):
            print(f'⏭️ スキップ: {item["title"]}')
            continue
        try:
            ja_text = translate_to_ja(item['title'], item['link'])
            post_to_discord(ja_text, item['link'])
            save_post(item['title'], item['link'])
            print(f'✅ 通知成功: {item["title"]}')
        except Exception as e:
            print(f'❌ 通知失敗: {e}')


if __name__ == '__main__':
    main()
