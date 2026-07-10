import requests
from bs4 import BeautifulSoup
import os
import urllib3

# SSL সার্টিফিকেট ভেরিফিকেশন এরর এড়াতে ওয়ার্নিং মেসেজ বন্ধ করা হয়েছে
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- কনফিগারেশন ---
URL = "https://pmeat.gov.bd/site/view/notices"
TELEGRAM_TOKEN = "8878360729:AAGyjB-XCR_rwu7Cn2yu8fEyokmj07mNtIA"  # আপনার নতুন বটের টোকেন
CHAT_ID = "6382850126"                             # আপনার চ্যাট আইডি
TRACK_FILE = "pmeat_notices_final.txt"              # 💡 ট্র্যাক ফাইলের নাম পরিবর্তন করা হয়েছে যেন আগের পুরানো ডাটা ভুলে নতুন করে মেসেজ পাঠায়

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
        
        # verify=False দিয়ে সরকারি সাইটের SSL সার্টিফিকেট বাইপাস করা হয়েছে
        response = requests.get(URL, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            print(f"❌ ওয়েবসাইটে প্রবেশ করা যাচ্ছে না। স্ট্যাটাস কোড: {response.status_code}")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            new_count = 0
            
            # reversed(rows) এর মাধ্যমে পুরানো থেকে নতুনের দিকে (নিচ থেকে উপরে) লুপ চলবে
            for row in reversed(rows):
                columns = row.find_all('td')
                
                # যদি টেবিল ডেটা বা কলাম সংখ্যা কম হয়, তবে স্কিপ করবে
                if len(columns) < 2:
                    continue
                
                link_element = row.find('a', href=True)
                if link_element:
                    # 💡 টাইটেল এবং লিংক আলাদা করা
                    title = link_element.text.strip()
                    link = link_element['href']
                    
                    # 💡 কলাম থেকে তারিখ খুঁজে বের করার নিখুঁত লজিক
                    published_date = "পাওয়া যায়নি"
                    for col in columns:
                        col_text = col.text.strip()
                        # যদি কলামের লেখায় সন বা ড্যাশ থাকে এবং টেক্সট সাইজ ছোট হয় (তারিখের ফরম্যাট)
                        if ("২০২" in col_text or "-" in col_text) and len(col_text) < 30 and col_text != title:
                            published_date = col_text
                            break
                    
                    # ব্যাকআপ অপশন: যদি লজিক কাজ না করে তবে সরাসরি ৩ নম্বর কলামের ডাটা নিবে
                    if published_date == "পাওয়া যায়নি" and len(columns) >= 3:
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
                    
                    # 🔔 টেলিগ্রাম মেসেজ ফরম্যাট (শিরোনাম প্রথমে, সঠিক তারিখ পরে)
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
