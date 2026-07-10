import requests
from bs4 import BeautifulSoup
import os
import urllib3

# SSL সার্টিফিকেট ভেরিফিকেশন এরর এড়াতে ওয়ার্নিং মেসেজ বন্ধ করা হয়েছে
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- কনফিগারেশন ---
URL = "https://pmeat.gov.bd/site/view/notices"
TELEGRAM_TOKEN = "8878360729:AAGyjB-XCR_rwu7Cn2yu8fEyokmj07mNtIA"  # আপনার বটের টোকেন
CHAT_ID = "6382850126"                             # আপনার চ্যাট আইডি
TRACK_FILE = "pmeat_notices_fixed.txt"              # 💡 নতুন ট্র্যাকিং ফাইল নাম যেন টেস্ট রান সফল হয়

# ফাইল চেক এবং রিড
if os.path.exists(TRACK_FILE):
    with open(TRACK_FILE, "r", encoding="utf-8") as f:
        sent_notices = set(f.read().splitlines())
else:
    sent_notices = set()

def send_telegram_message(text):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(telegram_url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ টেলিগ্রাম এরর: {e}")

def check_recent_notice():
    global sent_notices
    print("🔄 PMEAT ওয়েবসাইটের নোটিশ চেক করা হচ্ছে...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(URL, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            print(f"❌ ওয়েবসাইটে প্রবেশ করা যাচ্ছে না। স্ট্যাটাস কোড: {response.status_code}")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            new_count = 0
            
            # পুরানো থেকে নতুনের দিকে (নিচ থেকে উপরে) লুপ চলবে
            for row in reversed(rows):
                columns = row.find_all('td')
                
                # সরকারি সাইটের নোটিশ বোর্ডে সাধারণত ৩টি কলাম থাকে (ক্রমিক, শিরোনাম, তারিখ)
                # তাই কমপক্ষে ৩টি কলাম না থাকলে তা স্কিপ করবে
                if len(columns) < 3:
                    continue
                
                link_element = row.find('a', href=True)
                if link_element:
                    link = link_element['href']
                    
                    # 💡 নিখুঁত কলাম ইনডেক্স লজিক:
                    # ২য় কলামে (index 1) থাকে নোটিশের মূল শিরোনাম/বিষয়
                    title = columns[1].text.strip()
                    
                    # ৩য় কলামে (index 2) থাকে প্রকাশের তারিখ
                    published_date = columns[2].text.strip()
                    
                    # সাইটের ডোমেইন লিংক ঠিক করা
                    if link.startswith('/'):
                        link = f"https://pmeat.gov.bd{link}"
                    elif not link.startswith('http'):
                        link = f"https://pmeat.gov.bd/site/view/notices/{link}"
                        
                    # সার্কুলার বাদ দেওয়ার ফিল্টার
                    if "circular" in title.lower() or "সার্কুলার" in title:
                        continue
                        
                    # অলরেডি পাঠানো নোটিশ হলে স্কিপ করবে
                    if link in sent_notices:
                        continue
                    
                    # 🔔 টেলিগ্রাম মেসেজ ফরম্যাট
                    message = (
                        f"🔔 *PMEAT নতুন নোটিশ প্রকাশিত হয়েছে!*\n\n"
                        f"📌 *শিরোনাম:* {title}\n\n"
                        f"📅 *প্রকাশের তারিখ:* {published_date}\n"
                        f"🔗 *লিংক:* {link}"
                    )
                    
                    send_telegram_message(message)
                    print(f"✅ নতুন বটে পাঠানো হয়েছে: {title}")
                    
                    # ট্র্যাকিং ফাইলে সেভ করা
                    with open(TRACK_FILE, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    sent_notices.add(link)
                    new_count += 1
            
            if new_count == 0:
                print("ℹ️ নতুন কোনো নোটিশ পাওয়া যায়নি।")
        else:
            print("❌ নোটিশ টেবিলটি খুঁজে পাওয়া যায়নি।")
            
    except Exception as e:
        print(f"❌ ত্রুটি: {e}")

if __name__ == "__main__":
    check_recent_notice()
