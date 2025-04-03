import feedparser
import requests
import tweepy

# === APIキー ===
DEEPSEEK_API_KEY = 'ここにDeepseekのAPIキーを貼る'
X_API_KEY = 'ここにX APIキー'
X_API_SECRET = 'ここにX APIシークレット'
X_ACCESS_TOKEN = 'ここにXアクセストークン'
X_ACCESS_SECRET = 'ここにXアクセストークンシークレット'

# === RSS URL ===
rss_urls = [
    'https://hiphopdx.com/rss',
    'https://www.complex.com/music/rss',
    'https://pitchfork.com/rss/news/',
]

# === RSS取得 ===
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

# === Deepseekで翻訳 ===
def translate_with_deepseek(title, link):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
    }
    prompt = f"""
    以下の英語ニュースを日本語のヒップホップファン向けにSNS投稿用として簡潔に翻訳してください。
    スラングやカルチャー用語の雰囲気を崩さないように注意してください。

    タイトル: {title}
    URL: {link}
    """

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200
    }

    response = requests.post('https://api.deepseek.com/chat/completions', headers=headers, json=data)
    result = response.json()
    translation = result['choices'][0]['message']['content'].strip()

    return translation + f'\n\n詳細: {link}\n#HIPHOP #速報'

# === 投稿 ===
def post_tweet(content):
    auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)
    api = tweepy.API(auth)
    api.update_status(status=content)

# === メイン処理 ===
def main():
    news_items = fetch_news(rss_urls)
    for item in news_items:
        try:
            post_content = translate_with_deepseek(item['title'], item['link'])
            post_tweet(post_content)
            print(f'✅投稿成功：{item["title"]}')
        except Exception as e:
            print(f'❌投稿失敗：{e}')

if __name__ == '__main__':
    main()
