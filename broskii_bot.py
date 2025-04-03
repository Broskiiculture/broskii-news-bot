import feedparser
import requests
import tweepy
import os

# === APIキー ===
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_SECRET = os.getenv('X_ACCESS_SECRET')

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
あなたはアメリカのヒップホップシーンに詳しい音楽ライターです。
以下の英語ニュースを、日本語圏のヒップホップファンがRTしたくなるようなSNS投稿用の文面に翻訳してください。

【翻訳時のポイント】
・日本語は20代のヒップホップ好きの若者が日常的に使う口語体。
・少しオタクっぽく、ユーモアを含めてもOK。
・速報性を感じさせる簡潔な表現を使う。
・固有名詞やスラング、カルチャー用語は日本語圏のヒップホップファンが使う一般的な表記にする（例：Drake→ドレイク, beef→ビーフ, leak→リーク, Diss→ディス）。
・投稿の最後に、日本語のヒップホップファンが好むハッシュタグを最低2個つける（例：#HIPHOP速報 #USラップ最新情報）。
・ニュースのタイトルが分かりにくければ、提供されたURL先の内容を確認して正確に翻訳する。

【翻訳するニュース】
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
