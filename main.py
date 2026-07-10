import requests
from bs4 import BeautifulSoup
import os
import time
import urllib3

# SSL ওয়ার্নিং হাইড করার জন্য (কনসোল পরিষ্কার রাখতে)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- কনফিগারেশন ---
URL = "https://pmeat.gov.bd/pages/notices"
TELEGRAM_TOKEN = os.getenv("8878360729:AAGyjB-XCR_rwu7Cn2yu8fEyokmj07mNtIA")
CHAT_ID = os.getenv("6382850126")
TRACK_FILE = "sent_notices.txt"

if os.path.exists(TRACK_FILE):
    with open(TRACK_FILE, "r", encoding="utf-8") as f:
        sent_notices = set(f.read().splitlines())
else:
    sent_notices = set()

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Telegram Secrets not found!")
        return
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"❌ Telegram Error: {res.text}")
    except Exception as e:
        print(f"❌ Telegram Connection Error: {e}")

def scrape_pmeat_notices():
    global sent_notices
    print("🔄 PMEAT নোটিশ চেক করা হচ্ছে (SSL ভেরিফিকেশন ব্যপাস সচল)...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        # 👈 এখানে verify=False যোগ করা হয়েছে SSL সমস্যা এড়াতে
        response = requests.get(URL, headers=headers, timeout=20, verify=False) 
        
        if response.status_code != 200:
            print(f"❌ ওয়েবসাইটে প্রবেশ করা যাচ্ছে না। কোড: {response.status_code}")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        notice_elements = soup.find_all('a', href=True)
        new_notices = []

        for element in notice_elements:
            title = element.text.strip()
            link = element['href']
            
            if "/pages/notices/" in link or "files" in link:
                if not title or len(title) < 5:
                    continue
                
                if link.startswith('/'):
                    link = f"https://pmeat.gov.bd{link}"
                elif not link.startswith('http'):
                    link = f"https://pmeat.gov.bd/pages/notices/{link}"
                
                if link in sent_notices:
                    continue
                    
                new_notices.append({"title": title, "link": link})

        print(f"🎯 মোট নতুন নোটিশ পাওয়া গেছে: {len(new_notices)} টি")
        
        for notice in reversed(new_notices):
            message = f"🔔 *PMEAT নতুন নোটিশ!*\n\n📌 *শিরোনাম:* {notice['title']}\n\n🔗 *লিংক:* {notice['link']}"
            
            send_telegram_message(message)
            print(f"✅ টেলিগ্রামে পাঠানো হয়েছে: {notice['title']}")
            
            with open(TRACK_FILE, "a", encoding="utf-8") as f:
                f.write(notice['link'] + "\n")
            sent_notices.add(notice['link'])
            
            time.sleep(2)

    except Exception as e:
        print(f"❌ স্ক্রিপ্ট রান করতে সমস্যা: {e}")

if __name__ == "__main__":
    scrape_pmeat_notices()
