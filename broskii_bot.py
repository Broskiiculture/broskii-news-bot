import os
import feedparser
import requests
import tweepy

# === APIキー ===
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_SECRET = os.getenv('X_ACCESS_SECRET')

# === RSS ===
rss_urls = [
    'https://hiphopdx.com/rss',
    'https://www.complex.com/music/rss',
    'https://pitchfork.com/rss/news/',
]

# === ニュース取得 ===
def fetch_news(rss_urls):
    news_items = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news_items.append({
                'title': entry.title,
                'link': entry.link
            })
    return news_items

# === OpenRouterで日本語翻訳生成 ===
def translate_with_openrouter(title, link):
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    prompt = f"""
    あなたはアメリカのHIPHOP情報に詳しい日本人ライターです。
    以下の英語のニュースタイトルとURLから、X（旧Twitter）向けの日本語投稿文を作ってください。
    
    【ルール】
    - 速報感が伝わる
    - 日本のHIPHOP好きがRTしたくなるような口語体
    - US HIPHOPファン向けのスラングや言い回しもOK
    - 末尾に #HIPHOP #速報 のタグをつける

    【タイトル】{title}
    【URL】{link}
    """

    data = {
    "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()

    if 'choices' not in result:
        raise Exception(f"OpenRouter API Error: {result}")

    content = result['choices'][0]['message']['content'].strip()
    return content

# === 投稿 ===
def post_tweet(content):
    auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)
    api = tweepy.API(auth)
    api.update_status(status=content)

# === メイン ===
def main():
    news_items = fetch_news(rss_urls)
    for item in news_items:
        try:
            post_content = translate_with_openrouter(item['title'], item['link'])
            post_tweet(post_content)
            print(f'✅投稿成功：{item["title"]}')
        except Exception as e:
            print(f'❌投稿失敗：{e}')

if __name__ == '__main__':
    main()
