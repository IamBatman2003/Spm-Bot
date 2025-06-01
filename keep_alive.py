from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "✅ I'm alive!"

def run():
    # Flask will print “* Running on http://0.0.0.0:8080 …”
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    # Give Flask a heartbeat to start
    time.sleep(0.5)
    print("🟢 keep_alive thread started (Flask should be listening on 0.0.0.0:8080)")
    