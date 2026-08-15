import urllib.request
import xml.etree.ElementTree as ET
import json
import logging
import requests

FEEDS = [
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/"
]

MENTOR_URL = "http://100.73.54.72:8081/v1/chat/completions"

def fetch_rss_headlines():
    headlines = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
            root = ET.fromstring(html)
            for item in root.findall('.//item')[:5]:
                title = item.find('title')
                if title is not None and title.text:
                    headlines.append(title.text.strip())
        except Exception as e:
            logging.error(f"Error fetching RSS from {url}: {e}")
    return list(set(headlines))[:8] # unique top 8

def analyze_sentiment_local(headlines):
    if not headlines:
        return 0.0, "Nessuna notizia recente trovata."
        
    prompt = f"""You are the Sentiment Analyst Agent of the Nemotron Sovereign Broker ecosystem.
Analyze the following latest crypto news headlines and determine the aggregate market sentiment.

Headlines:
{json.dumps(headlines, indent=2)}

Output strictly a JSON object with:
- "sentiment_score": a float between -1.0 (extremely bearish/panic) and +1.0 (extremely bullish/fomo).
- "reason": a short, concise explanation in Italian of why you chose this score based on the headlines.

Only return raw JSON. No markdown or code block wrappers."""
    try:
        resp = requests.post(MENTOR_URL, json={
            "model": "/opt/kraken-inference/models/Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "messages": [
                {"role": "system", "content": "You are the local Sentiment Analyst Agent of the Nemotron Sovereign Broker ecosystem. Speak in Italian."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 300
        }, timeout=30)
        content = resp.json()["choices"][0]["message"]["content"]
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace('```json','').replace('```','').strip()
        data = json.loads(content)
        return float(data.get("sentiment_score", 0.0)), data.get("reason", "Analisi completata.")
    except Exception as e:
        logging.error(f"Error in local sentiment analysis: {e}")
        return 0.0, f"Errore nell'analisi locale: {e}"

def get_market_sentiment():
    try:
        headlines = fetch_rss_headlines()
        score, reason = analyze_sentiment_local(headlines)
        return {"score": score, "reason": reason, "headlines": headlines}
    except Exception as e:
        logging.error(f"Failed to get market sentiment: {e}")
        return {"score": 0.0, "reason": str(e), "headlines": []}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(get_market_sentiment())
