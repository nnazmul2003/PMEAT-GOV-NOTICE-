import requests
from bs4 import BeautifulSoup
import os
import urllib3

# SSL সার্টিফিকেট ওয়ার্নিং মেসেজগুলো হাইড করার জন্য
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- কনফিগারেশন ---
URL = "https://pmeat.gov.bd/site/view/notices"
TELEGRAM_TOKEN = "8878360729:AAGyjB-XCR_rwu7Cn2yu8fEyokmj07mNtIA"  
CHAT_ID = "6382850126"                             
TRACK_FILE = "pmeat_notices.txt"                    

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
            
            for row in reversed(rows):
                columns = row.find_all('td')
                
                # টেবিলে কমপক্ষে ৩টি কলাম থাকতে হবে (ক্রমিক, শিরোনাম/তারিখ ইত্যাদি)
                if len(columns) < 2:
                    continue
                
                link_element = row.find('a', href=True)
                if link_element:
                    # 💡 টাইটেল এবং লিংক বের করা
                    title = link_element.text.strip()
                    link = link_element['href']
                    
                    # 💡 PMEAT সাইটের সঠিক কলাম থেকে তারিখ আলাদা করার লজিক
                    # সাধারণত শেষ কলামে অথবা ২য় কলামে যদি তারিখের ফরম্যাট (যেমন: ২০২৬ বা ২০২৫) থাকে
                    published_date = "পাওয়া যায়নি"
                    for col in columns:
                        col_text = col.text.strip()
                        # যদি কলামের লেখায় সাধারণ বাংলা সন/তারিখের মতো ফরম্যাট থাকে এবং তা টাইটেল না হয়
                        if ("২০২" in col_text or "-" in col_text) and len(col_text) < 30 and col_text != title:
                            published_date = col_text
                            break
                    
                    # যদি উপরে তারিখ নিখুঁতভাবে না মেলে, তবে ৩ নম্বর কলাম ট্রাই করবে
                    if published_date == "পাওয়া যায়নি" and len(columns) >= 3:
                        published_date = columns[2].text.strip()

                    if link.startswith('/'):
                        link = f"https://pmeat.gov.bd{link}"
                    elif not link.startswith('http'):
                        link = f"https://pmeat.gov.bd/site/view/notices/{link}"
                        
                    if "circular" in title.lower() or "সার্কুলার" in title:
                        continue
                        
                    if link in sent_notices:
                        continue
                    
                    # 🔔 সুন্দর মেসেজ ফরম্যাট
                    message = (
                        f"🔔 *PMEAT নতুন নোটিশ প্রকাশিত হয়েছে!*\n\n"
                        f"📌 *শিরোনাম:* {title}\n\n"
                        f"📅 *প্রকাশের তারিখ:* {published_date}\n"
                        f"🔗 *লিংক:* {link}"
                    )
                    
                    send_telegram_message(message)
                    print(f"✅ নতুন বটে পাঠানো হয়েছে: {title}")
                    
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
