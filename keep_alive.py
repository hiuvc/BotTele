# keep_alive.py
from flask import Flask
from threading import Thread
from datetime import datetime

app = Flask('')

@app.route('/')
def home():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[KEEP_ALIVE] Ping received at {now}")
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
