`python
import feedparser
import requests
import os
import json
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# Конфигурация
RSS_FEEDS = [
    {
        'url': 'https://openai.com/blog/rss.xml',
        'name': '🤖 OpenAI'
    },
    {
        'url': 'https://blog.google/technology/ai/rss/',
        'name': '🔍 Google AI'
    },
    {
        'url': 'https://deepmind.com/blog/feed/basic/',
        'name': '🧠 DeepMind'
    }
]

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Сообщение отправлено")
        else:
            print(f"❌ Ошибка отправки: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
      def load_sent_articles():
    """Загрузка списка уже отправленных статей"""
    try:
        with open('sent_articles.json', 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_sent_articles(articles):
    """Сохранение списка отправленных статей"""
    with open('sent_articles.json', 'w') as f:
        json.dump(list(articles), f)

def fetch_and_send_news():
    """Основная функция получения и отправки новостей"""
    sent_articles = load_sent_articles()
    new_articles = []
    
    # Получаем статьи за последние 6 часов
    cutoff_time = datetime.now() - timedelta(hours=6)
    
    for feed_config in RSS_FEEDS:
        try:
            print(f"🔄 Проверяем {feed_config['name']}...")
            feed = feedparser.parse(feed_config['url'])
            
            for entry in feed.entries[:5]:  # Последние 5 статей
                article_id = entry.link
                
                # Пропускаем уже отправленные
                if article_id in sent_articles:
                    continue
                
                # Проверяем дату публикации
                try:
                    if hasattr(entry, 'published'):
                        pub_date = date_parser.parse(entry.published).replace(tzinfo=None)
                        if pub_date < cutoff_time:
                            continue
                except:
                    pass  # Если не удалось парсить дату, отправляем статью
                
                # Формируем сообщение
                title = entry.title
                link = entry.link
                summary = entry.summary if hasattr(entry, 'summary') else ""
                
                # Обрезаем длинное описание
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                
                message = f"""
{feed_config['name']} <b>{title}</b>

{summary}

🔗 <a href="{link}">Читать полностью</a>
                """.strip()
                
                new_articles.append({
                    'id': article_id,
                    'message': message
                })
                
        except Exception as e:
            print(f"❌ Ошибка при обработке {feed_config['name']}: {e}")
    
    # Отправляем новые статьи
    if new_articles:
        print(f"📨 Найдено {len(new_articles)} новых статей")
        
        for article in new_articles:
            send_telegram_message(article['message'])
            sent_articles.add(article['id'])
        
        # Сохраняем обновленный список
        save_sent_articles(sent_articles)
        
    else:
        print("📭 Новых статей нет")

if name == "main":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Не настроены переменные окружения!")
        exit(1)
    
    fetch_and_send_news()
