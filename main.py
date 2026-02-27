import telebot
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from flask import Flask
import threading

# টেলিগ্রাম থেকে পাওয়া টোকেন এখানে দিন
TOKEN = "YOUR_API_TOKEN"
bot = telebot.TeleBot(TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.send_message(message.chat.id, "স্বাগতম! আপনার ইনস্টাগ্রাম ইউজারনেম দিন:")
    bot.register_next_step_handler(msg, get_user)

def get_user(message):
    user_data[message.chat.id] = {'user': message.text}
    msg = bot.send_message(message.chat.id, "এখন আপনার পাসওয়ার্ড দিন:")
    bot.register_next_step_handler(msg, get_pass)

def get_pass(message):
    user_id = message.chat.id
    user_data[user_id]['pass'] = message.text
    bot.send_message(user_id, "লগইন করার চেষ্টা করছি... অপেক্ষা করুন।")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    user_data[user_id]['driver'] = driver

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(6)
        driver.find_element(By.NAME, "username").send_keys(user_data[user_id]['user'])
        driver.find_element(By.NAME, "password").send_keys(user_data[user_id]['pass'])
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)

        # যদি ওটিপি (OTP) লাগে
        if "checkpoint" in driver.current_url or "two_factor" in driver.current_url:
            msg = bot.send_message(user_id, "কোড প্রয়োজন! আপনার ইমেইল/নাম্বারে যাওয়া কোডটি এখানে দিন:")
            bot.register_next_step_handler(msg, get_otp)
        else:
            finish_login(user_id)
    except:
        bot.send_message(user_id, "লগইন ব্যর্থ। আবার চেষ্টা করুন।")
        driver.quit()

def get_otp(message):
    user_id = message.chat.id
    otp = message.text
    driver = user_data[user_id]['driver']
    try:
        driver.find_element(By.NAME, "verificationCode").send_keys(otp)
        driver.find_element(By.XPATH, "//button[text()='Confirm']").click()
        time.sleep(8)
        finish_login(user_id)
    except:
        bot.send_message(user_id, "ভুল কোড বা সেশন আউট।")
        driver.quit()

def finish_login(user_id):
    driver = user_data[user_id]['driver']
    cookies = driver.get_cookies()
    cookie_file = f"cookies_{user_id}.json"
    with open(cookie_file, "w") as f:
        json.dump(cookies, f)
    with open(cookie_file, "rb") as f:
        bot.send_document(user_id, f, caption="সফল! আপনার কুকি ফাইল।")
    driver.quit()

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"
def run_flask(): app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
