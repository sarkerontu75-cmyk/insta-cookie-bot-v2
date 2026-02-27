import telebot
from telebot import types
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from flask import Flask
import threading

TOKEN = "আপনার_বট_টোকেন"
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
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "বটটি রিসেট করা হয়েছে। নিচের বাটন থেকে শুরু করুন:", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == '🚀 Start Extraction')
def ask_user(message):
    msg = bot.send_message(message.chat.id, "আপনার ইনস্টাগ্রাম ইউজারনেম দিন:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, get_user)

def get_user(message):
    user_id = message.chat.id
    user_data[user_id] = {'user': message.text}
    msg = bot.send_message(user_id, "এখন আপনার পাসওয়ার্ড দিন:")
    bot.register_next_step_handler(msg, get_pass)

def get_pass(message):
    user_id = message.chat.id
    user_data[user_id]['pass'] = message.text
    bot.send_message(user_id, "লগইন প্রসেস শুরু হচ্ছে... এটি ১-২ মিনিট সময় নিতে পারে।")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # স্ক্রিন সাইজ ফিক্স করা হয়েছে
    driver = webdriver.Chrome(options=options)
    user_data[user_id]['driver'] = driver

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(8)
        driver.find_element(By.NAME, "username").send_keys(user_data[user_id]['user'])
        driver.find_element(By.NAME, "password").send_keys(user_data[user_id]['pass'])
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(12)

        if "checkpoint" in driver.current_url or "two_factor" in driver.current_url:
            msg = bot.send_message(user_id, "⚠️ নিরাপত্তা কোড (OTP) প্রয়োজন! আপনার ইমেইল/ফোনে যাওয়া কোডটি এখানে লিখুন:")
            bot.register_next_step_handler(msg, get_otp)
        else:
            finish_login(user_id)
    except Exception as e:
        bot.send_message(user_id, "❌ লগইন ব্যর্থ হয়েছে। সম্ভবত পাসওয়ার্ড ভুল বা নেটওয়ার্ক ইস্যু। আবার ট্রাই করুন।", reply_markup=main_menu())
        driver.quit()

def get_otp(message):
    user_id = message.chat.id
    otp = message.text
    driver = user_data[user_id]['driver']
    try:
        driver.find_element(By.NAME, "verificationCode").send_keys(otp)
        driver.find_element(By.XPATH, "//button[text()='Confirm']").click()
        time.sleep(10)
        finish_login(user_id)
    except:
        bot.send_message(user_id, "❌ ওটিপি ভুল বা কাজ করেনি।", reply_markup=main_menu())
        driver.quit()

def finish_login(user_id):
    driver = user_data[user_id]['driver']
    try:
        cookies = driver.get_cookies()
        if not cookies:
            raise Exception("No cookies found")
            
        cookie_file = f"cookies_{user_id}.json"
        with open(cookie_file, "w") as f:
            json.dump(cookies, f, indent=4)
        
        with open(cookie_file, "rb") as f:
            bot.send_document(user_id, f, caption="✅ সফল! আপনার কুকি ফাইলটি পাঠানো হলো।", reply_markup=main_menu())
        os.remove(cookie_file)
    except:
        bot.send_message(user_id, "❌ লগইন হয়েছে কিন্তু কুকি সংগ্রহ করা যায়নি। আবার চেষ্টা করুন।", reply_markup=main_menu())
    finally:
        driver.quit()

# Render Health Check
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"
def run_flask(): app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
