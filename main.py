from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os
import asyncio
import random

from keep_alive import keep_alive

# 1) Start the Flask “keep_alive” thread immediately
keep_alive()

# 2) (Optional) Debug: print environment variables
print("\n" + "="*40)
print("🔥 DEBUG: Checking Environment Variables")
print("="*40)
env_vars = ['GROUP_LINK', 'ALLOWED_USER_ID',
            'USER1_ID', 'USER1_HASH', 'SESSION_1',
            'USER2_ID', 'USER2_HASH', 'SESSION_2',
            'USER3_ID', 'USER3_HASH', 'SESSION_3',
            'USER4_ID', 'USER4_HASH', 'SESSION_4']
for var in env_vars:
    exists = "✅" if os.getenv(var) else "❌"
    if 'HASH' in var or 'SESSION' in var:
        value = '******* (hidden)' if os.getenv(var) else 'MISSING'
    else:
        value = os.getenv(var) or 'MISSING'
    print(f"{exists} {var}: {value}")
print("="*40 + "\n")

# 3) Load your config
GROUP_LINK    = os.getenv("GROUP_LINK", "https://t.me/+q04dFMa8tKdhNTU1")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "1745055042"))

# 4) Initialize TelegramClient for each account
clients = {}
accounts = [
    {"name": "User1", "id": "USER1_ID", "hash": "USER1_HASH", "session": "SESSION_1"},
    {"name": "User2", "id": "USER2_ID", "hash": "USER2_HASH", "session": "SESSION_2"},
    {"name": "User3", "id": "USER3_ID", "hash": "USER3_HASH", "session": "SESSION_3"},
    {"name": "User4", "id": "USER4_ID", "hash": "USER4_HASH", "session": "SESSION_4"}
]
for acc in accounts:
    try:
        api_id      = int(os.getenv(acc["id"]))
        api_hash    = os.getenv(acc["hash"])
        session_str = os.getenv(acc["session"])
        if not (api_id and api_hash and session_str):
            print(f"❌ {acc['name']}: Missing credentials, skipping")
            continue
        clients[acc["name"]] = TelegramClient(
            StringSession(session_str),
            api_id,
            api_hash
        )
        print(f"✅ {acc['name']} client initialized")
    except Exception as e:
        print(f"⛔ {acc['name']} initialization failed: {e}")

if not clients:
    print("\n💥 CRITICAL ERROR: No clients initialized! Exiting…")
    exit(1)

# 5) Simple message-sending loop (demo only)
user_messages = {
    "User1": ["Hello from User1!", "Beat everybody!"],
    "User2": ["Hey all, this is User2."],
    "User3": ["What’s up? User3 here."],
    "User4": ["User4 checking in."]
}
spam_active = False
stop_event = asyncio.Event()
spam_tasks = []

async def send_messages_forever(client, name, messages, stop_event):
    try:
        group = await client.get_entity(GROUP_LINK)
        print(f"[✅] {name} connected to group")
    except Exception as e:
        print(f"[❌] {name} failed to connect to group: {e}")
        return
    try:
        while not stop_event.is_set():
            msg = random.choice(messages)
            try:
                await client.send_message(group, msg)
                print(f"[📩] {name} sent: {msg}")
            except Exception as e:
                print(f"[⚠️] {name} error: {e}")
            # Faster sending interval here
            await asyncio.sleep(random.uniform(0.8, 1.5))
    except asyncio.CancelledError:
        print(f"[🛑] {name} send_messages task cancelled")

async def start_handler(event):
    global spam_active, spam_tasks
    sender = await event.get_sender()
    if sender.id != ALLOWED_USER_ID:
        await event.respond("🚫 Unauthorized")
        return
    if spam_active:
        await event.respond("⚠️ Already running")
        return
    spam_active = True
    stop_event.clear()
    await event.respond("🚀 Spamming started…")

    spam_tasks = []
    for name, client in clients.items():
        task = asyncio.create_task(send_messages_forever(client, name, user_messages[name], stop_event))
        spam_tasks.append(task)

async def stop_handler(event):
    global spam_active, spam_tasks
    sender = await event.get_sender()
    if sender.id != ALLOWED_USER_ID:
        await event.respond("🚫 Unauthorized")
        return
    if not spam_active:
        await event.respond("⚠️ Not running")
        return
    spam_active = False
    stop_event.set()
    for task in spam_tasks:
        task.cancel()
    spam_tasks = []
    await event.respond("🛑 Spamming stopped")

def register_handlers(client):
    @client.on(events.NewMessage(pattern=r'(?i)^(/start|a)$'))
    async def on_start(event):
        await start_handler(event)

    @client.on(events.NewMessage(pattern=r'(?i)^(/stop|s)$'))
    async def on_stop(event):
        await stop_handler(event)

async def main():
    print("\n🔌 Connecting clients…")
    failed = []
    for name, client in clients.items():
        try:
            await client.start()
            register_handlers(client)
            print(f"[🔑] {name} logged in")
        except Exception as e:
            print(f"⛔ {name} login failed: {e}")
            failed.append(name)
    for name in failed:
        del clients[name]
    if not clients:
        print("\n💥 FATAL: No clients remain. Exiting…")
        return
    print("\n🤖 Bot is now ACTIVE on all accounts")
    await asyncio.gather(*[c.run_until_disconnected() for c in clients.values()])

if __name__ == '__main__':
    print("\n⚡ Starting bot loop…")
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"[🔥] Critical error: {e}")
            import time; time.sleep(5)
            