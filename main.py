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

TOKEN = "YOUR_BOT_TOKEN_HERE"
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
    bot.send_message(message.chat.id, "বট প্রস্তুত। লগইন শুরু করতে নিচের বাটনে চাপ দিন:", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == '🚀 Start Extraction')
def ask_user(message):
    msg = bot.send_message(message.chat.id, "👤 আপনার ইনস্টাগ্রাম ইউজারনেম দিন:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, get_user)

def get_user(message):
    user_data[message.chat.id] = {'user': message.text}
    msg = bot.send_message(message.chat.id, "🔑 এখন পাসওয়ার্ড দিন:")
    bot.register_next_step_handler(msg, get_pass)

def get_pass(message):
    user_id = message.chat.id
    user_data[user_id]['pass'] = message.text
    bot.send_message(user_id, "⏳ সেশন তৈরি হচ্ছে... অপেক্ষা করুন।")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # মোবাইল ব্রাউজার হিসেবে পরিচয় দেওয়ার জন্য User-Agent
    options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    user_data[user_id]['driver'] = driver
    wait = WebDriverWait(driver, 25)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)
        
        # লগইন ইনপুট
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(user_data[user_id]['user'])
        driver.find_element(By.NAME, "password").send_keys(user_data[user_id]['pass'])
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(12)

        # ১. সাসপেন্ড বা আইডি নষ্ট ডিটেকশন
        current_url = driver.current_url
        page_content = driver.page_source.lower()
        if "suspended" in page_content or "checkpoint/disabled" in current_url:
            bot.send_message(user_id, "❌ দুঃখিত! এই আইডিটি বর্তমানে সাসপেন্ড বা নষ্ট অবস্থায় আছে।", reply_markup=main_menu())
            driver.quit()
            return

        # ২. ইমেইল অপশন সিলেক্ট করা (যদি অপশন থাকে)
        try:
            email_option = driver.find_elements(By.XPATH, "//span[contains(text(), 'Email')] | //label[contains(text(), 'email')]")
            if email_option:
                email_option[0].click()
                time.sleep(2)
                driver.find_element(By.XPATH, "//button[contains(text(), 'Send Security Code')]").click()
                bot.send_message(user_id, "📧 আপনার ইমেইলে একটি কোড পাঠানো হয়েছে। সেটি এখানে দিন:")
                bot.register_next_step_handler(message, get_otp)
                return
        except: pass

        # ৩. যদি সরাসরি ওটিপি পেজে যায়
        if "two_factor" in current_url or "checkpoint" in current_url:
            bot.send_message(user_id, "⚠️ আপনার ইমেইল বা ফোনে যাওয়া কোডটি এখানে দিন:")
            bot.register_next_step_handler(message, get_otp)
        else:
            handle_popups_and_finish(user_id)

    except Exception as e:
        bot.send_message(user_id, "❌ লগইন ব্যর্থ। তথ্য চেক করে আবার চেষ্টা করুন।", reply_markup=main_menu())
        driver.quit()

def get_otp(message):
    user_id = message.chat.id
    otp = message.text
    driver = user_data[user_id]['driver']
    try:
        driver.find_element(By.NAME, "verificationCode").send_keys(otp)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')] | //button[@type='button']").click()
        time.sleep(12)
        handle_popups_and_finish(user_id)
    except:
        bot.send_message(user_id, "❌ কোড ভুল হয়েছে।", reply_markup=main_menu())
        driver.quit()

def handle_popups_and_finish(user_id):
    driver = user_data[user_id]['driver']
    try:
        # সকল পপ-আপ অটো স্কিপ
        popups = ["Not Now", "Save Info", "Cancel", "Dismiss"]
        for p in popups:
            try:
                btn = driver.find_elements(By.XPATH, f"//button[contains(text(), '{p}')]")
                if btn: 
                    btn[0].click()
                    time.sleep(3)
            except: pass

        cookies = driver.get_cookies()
        if cookies:
            cookie_file = f"cookies_{user_id}.json"
            with open(cookie_file, "w") as f:
                json.dump(cookies, f, indent=4)
            with open(cookie_file, "rb") as f:
                bot.send_document(user_id, f, caption="✅ সাকসেস! আপনার কুকি ফাইল পাঠানো হলো।", reply_markup=main_menu())
            os.remove(cookie_file)
        else:
            bot.send_message(user_id, "❌ লগইন সফল কিন্তু কুকি পাওয়া যায়নি।", reply_markup=main_menu())
    finally:
        driver.quit()

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Active"
def run_flask(): app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
