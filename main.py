import telebot
from telebot import types
import time, json, os, threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from flask import Flask

TOKEN = "8365369624:AAEwBNJuuuAHldM4PYDGtd9tU5LYOL8VpDM"
bot = telebot.TeleBot(TOKEN)
user_sessions = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add('🚀 Start', '▶️ Resume', '🔄 Reset')
    bot.send_message(message.chat.id, "🔥 টার্বো মোড রেডি। ৫-৭ সেকেন্ড টার্গেট!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🚀 Start')
def ask_user(message):
    msg = bot.send_message(message.chat.id, "👤 ইউজারনেম:")
    bot.register_next_step_handler(msg, get_user)

def get_user(message):
    user_sessions[message.chat.id] = {'user': message.text}
    msg = bot.send_message(message.chat.id, "🔑 পাসওয়ার্ড:")
    bot.register_next_step_handler(msg, get_pass)

def get_pass(message):
    user_id = message.chat.id
    user_sessions[user_id]['pass'] = message.text
    bot.send_message(user_id, "⚡ রকেট স্পিডে কাজ শুরু হচ্ছে...")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--page-load-strategy=eager") # পেজ অর্ধেক লোড হলেই কাজ শুরু করবে
    options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 11; SM-A515F)")
    
    # অপ্রয়োজনীয় সব বন্ধ (Fastest)
    prefs = {"profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    user_sessions[user_id]['driver'] = driver
    threading.Thread(target=turbo_login, args=(user_id,)).start()

def turbo_login(user_id):
    driver = user_sessions[user_id]['driver']
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(2.5) # মাত্র ২.৫ সেকেন্ড ওয়েট
        
        # সরাসরি ইনপুট
        driver.find_element(By.NAME, "username").send_keys(user_sessions[user_id]['user'])
        driver.find_element(By.NAME, "password").send_keys(user_sessions[user_id]['pass'])
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(4.5) # লগইন প্রসেস হওয়ার জন্য ৪.৫ সেকেন্ড
        check_status(user_id)
    except:
        bot.send_message(user_id, "❌ কানেকশন এরর। আবার ট্রাই করুন।")

def check_status(user_id):
    driver = user_sessions[user_id]['driver']
    cookies = driver.get_cookies()
    
    # সেশন আইডি পেলে সাথে সাথে ফাইল পাঠাবে
    if any(c['name'] == 'sessionid' for c in cookies):
        file_name = f"cookies_{user_id}.json"
        with open(file_name, "w") as f:
            json.dump(cookies, f, indent=4)
        bot.send_document(user_id, open(file_name, "rb"), caption="✅ সাকসেস! ৫ সেকেন্ডের মধ্যেই রেডি!")
        os.remove(file_name)
        driver.quit()
        del user_sessions[user_id]
    else:
        # না পেলে স্ক্রিনশট ও লিংক (যাতে আপনি ফিক্স করতে পারেন)
        path = f"ss_{user_id}.png"
        driver.save_screenshot(path)
        bot.send_photo(user_id, open(path, "rb"), caption=f"📍 এখানে আটকেছে। লিংক:\n{driver.current_url}\n\nসমাধান করে '▶️ Resume' দিন।")
        os.remove(path)

@bot.message_handler(func=lambda m: m.text == '▶️ Resume')
def resume(message):
    user_id = message.chat.id
    if user_id in user_sessions:
        bot.send_message(user_id, "🔄 আবার চেক করছি...")
        threading.Thread(target=check_status, args=(user_id,)).start()

@bot.message_handler(func=lambda m: m.text == '🔄 Reset')
def reset(message):
    start(message)

app = Flask(__name__)
@app.route('/')
def home(): return "Fast"
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    bot.polling(none_stop=True)
