import telebot
from telebot import types
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask
import threading

# আপনার টোকেন
TOKEN = "8365369624:AAEwBNJuuuAHldM4PYDGtd9tU5LYOL8VpDM"
bot = telebot.TeleBot(TOKEN)
user_data = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton('🚀 Start Extraction')
    item2 = types.KeyboardButton('🔄 Restart Bot')
    markup.add(item1, item2)
    return markup

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == '🔄 Restart Bot')
def start(message):
    bot.send_message(message.chat.id, "🔥 আল্ট্রা-ফাস্ট কুকি এক্সট্রাক্টর প্রস্তুত।", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == '🚀 Start Extraction')
def ask_user(message):
    msg = bot.send_message(message.chat.id, "👤 ইউজারনেম দিন:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, get_user)

def get_user(message):
    user_data[message.chat.id] = {'user': message.text}
    msg = bot.send_message(message.chat.id, "🔑 পাসওয়ার্ড দিন:")
    bot.register_next_step_handler(msg, get_pass)

def get_pass(message):
    user_id = message.chat.id
    user_data[user_id]['pass'] = message.text
    bot.send_message(user_id, "⚡ দ্রুত প্রসেসিং শুরু হচ্ছে...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    user_data[user_id]['driver'] = driver
    wait = WebDriverWait(driver, 20) # ফাস্ট রেসপন্স টাইম

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        
        # ইউজার-পাস ইনপুট
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(user_data[user_id]['user'])
        driver.find_element(By.NAME, "password").send_keys(user_data[user_id]['pass'])
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        time.sleep(10) # লগইন প্রসেসিং টাইম
        current_url = driver.current_url
        page_source = driver.page_source.lower()

        # ১. অন্য ডিভাইসে অ্যাপ্রুভাল চেক (Approval System)
        if "approve" in page_source or "another device" in page_source:
            bot.send_message(user_id, "📱 আপনার অন্য ডিভাইসে (App) অ্যাপ্রুভাল রিকোয়েস্ট গেছে। দ্রুত 'Approve' করুন এবং ১ মিনিট অপেক্ষা করুন।")
            # এখানে বট চেষ্টা করবে অন্য উপায়ে কোড পাঠানো যায় কি না
            try:
                try_another = driver.find_elements(By.XPATH, "//button[contains(text(), 'Try another way')]")
                if try_another:
                    try_another[0].click()
                    time.sleep(3)
                    email_btn = driver.find_elements(By.XPATH, "//span[contains(text(), 'Email')]")
                    if email_btn:
                        email_btn[0].click()
                        driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]").click()
                        bot.send_message(user_id, "📧 অন্য ডিভাইসের বদলে আপনার ইমেইলে কোড পাঠানো হয়েছে। কোডটি দিন:")
                        bot.register_next_step_handler(message, get_otp)
                        return
            except: pass
            return

        # ২. সরাসরি ইমেইল/ফোন ওটিপি (Direct OTP)
        if "checkpoint" in current_url or "two_factor" in current_url:
            bot.send_message(user_id, "📩 সরাসরি কোড পাঠানোর অপশন এসেছে। আপনার ইমেইল/ফোন চেক করে কোডটি দিন:")
            bot.register_next_step_handler(message, get_otp)
        else:
            handle_finish(user_id)

    except Exception as e:
        bot.send_message(user_id, "❌ লগইন ফেইল। আবার চেষ্টা করুন।", reply_markup=main_menu())
        driver.quit()

def get_otp(message):
    user_id = message.chat.id
    otp = message.text
    driver = user_data[user_id]['driver']
    try:
        driver.find_element(By.NAME, "verificationCode").send_keys(otp)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')] | //button[@type='button']").click()
        time.sleep(10)
        handle_finish(user_id)
    except:
        bot.send_message(user_id, "❌ ওটিপি কাজ করেনি।", reply_markup=main_menu())
        driver.quit()

def handle_finish(user_id):
    driver = user_data[user_id]['driver']
    try:
        # সকল পপ-আপ দ্রুত স্কিপ করা
        popups = ["Not Now", "Save Info", "Cancel"]
        for p in popups:
            try:
                btn = driver.find_elements(By.XPATH, f"//button[contains(text(), '{p}')]")
                if btn: btn[0].click(); time.sleep(2)
            except: pass

        cookies = driver.get_cookies()
        if cookies:
            file_name = f"cookies_{user_id}.json"
            with open(file_name, "w") as f:
                json.dump(cookies, f, indent=4)
            with open(file_name, "rb") as f:
                bot.send_document(user_id, f, caption="✅ সাকসেস! আপনার কুকি ফাইল।", reply_markup=main_menu())
            os.remove(file_name)
        else:
            bot.send_message(user_id, "❌ কুকি পাওয়া যায়নি।", reply_markup=main_menu())
    finally:
        driver.quit()

app = Flask(__name__)
@app.route('/')
def home(): return "Online"
def run_flask(): app.run(host='0.0.0.0', port=os.environ.get('PORT', 10000))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
