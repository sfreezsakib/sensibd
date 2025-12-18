import os
import json
import base64
import time
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from github import Github

# ============ CREDENTIALS ============
TELEGRAM_TOKEN = "8429248919:AAF403QR9g7FPxNDeLdiIIBBROu25Fbfit8"
# আপনার দেওয়া নতুন টোকেন (Token #5)
GITHUB_TOKEN = "Ghp_zT7kPcLPdsHwVuoP2NQAPW1p78Bg5v1ihD9N"
REPO_NAME = "sfreezsakib/sensibd"
# =====================================

# --- FAKE WEB SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# GitHub Connection
try:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception as e:
    print(f"GitHub Connection Error: {e}")

THUMBNAIL, TITLE_DEVICE, SECRET_IMG, LINKS = range(4)
EDIT_SELECT, EDIT_VALUE = range(4, 6)
temp_data = {}
edit_cache = {}

# --- UPLOAD COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 **Sensi Admin Panel**\nReady to upload!")

async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1️⃣ **Thumbnail** ছবি পাঠান।")
    return THUMBNAIL

async def receive_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return THUMBNAIL
    
    # --- ERROR FIX: await সরায়ে ফেলা হয়েছে ---
    photo_file = await update.message.photo[-1].get_file()
    file_byte_array = await photo_file.download_as_bytearray()
    
    fname = f"images/thumb_{int(time.time())}.jpg"
    
    try:
        # bytes() এ কনভার্ট করে আপলোড করা হচ্ছে
        repo.create_file(fname, "Add thumb", bytes(file_byte_array))
        
        temp_data['thumb'] = f"https://raw.githubusercontent.com/{REPO_NAME.split('/')[0]}/{REPO_NAME.split('/')[1]}/main/{fname}"
        await update.message.reply_text("✅ থাম্বনেইল সেভ।\n\n2️⃣ লিখুন: `Device | Title`")
        return TITLE_DEVICE
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return ConversationHandler.END

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if '|' not in update.message.text: 
        await update.message.reply_text("❌ ভুল ফরম্যাট! `Device | Title` এভাবে লিখুন।")
        return TITLE_DEVICE
    
    dev, tit = update.message.text.split('|', 1)
    temp_data.update({'device': dev.strip(), 'title': tit.strip(), 'id': int(time.time())})
    await update.message.reply_text("✅ টাইটেল সেভ।\n\n3️⃣ **Secret Image** পাঠান।")
    return SECRET_IMG

async def receive_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return SECRET_IMG
    
    # --- ERROR FIX ---
    photo_file = await update.message.photo[-1].get_file()
    file_byte_array = await photo_file.download_as_bytearray()
    
    fname = f"images/secret_{int(time.time())}.jpg"
    
    try:
        repo.create_file(fname, "Add secret", bytes(file_byte_array))
        
        temp_data['secret'] = f"https://raw.githubusercontent.com/{REPO_NAME.split('/')[0]}/{REPO_NAME.split('/')[1]}/main/{fname}"
        await update.message.reply_text("✅ সিক্রেট সেভ।\n\n4️⃣ লিংক দিন: `Sensi Link, Panel Link`")
        return LINKS
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return ConversationHandler.END

async def receive_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    s, p = (text.split(',', 1) if ',' in text else (text, "#"))
    temp_data.update({'sensi_link': s.strip(), 'panel_link': p.strip()})
    
    data = get_json()
    data.insert(0, temp_data.copy())
    save_json(data)
    
    await update.message.reply_text("🎉 **পোস্ট সাকসেসফুল!**")
    temp_data.clear()
    return ConversationHandler.END

# --- MANAGE COMMANDS ---
async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_json()
    if not data: return await update.message.reply_text("পোস্ট নেই।")
    for post in data[:5]:
        await update.message.reply_text(
            f"📱 {post['device']}\n📌 {post['title']}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{post['id']}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"del_{post['id']}")
            ]])
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if "_" not in query.data: return
    action, pid = query.data.split('_', 1)
    pid = int(pid)

    if action == "del":
        data = [p for p in get_json() if p['id'] != pid]
        save_json(data)
        await query.edit_message_text("🗑️ ডিলিট করা হয়েছে।")
    
    elif action == "edit":
        edit_cache['id'] = pid
        await query.edit_message_text("কি এডিট করবেন?", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Title", callback_data="type_title")],
            [InlineKeyboardButton("Links", callback_data="type_links")]
        ]))
        return EDIT_SELECT

async def edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    edit_cache['type'] = query.data
    await query.message.reply_text("নতুন ডাটা পাঠান:")
    return EDIT_VALUE

async def receive_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = edit_cache.get('id')
    etype = edit_cache.get('type')
    data = get_json()
    idx = next((i for i, item in enumerate(data) if item["id"] == pid), -1)
    
    if idx != -1:
        if etype == "type_title" and '|' in update.message.text:
            d, t = update.message.text.split('|', 1)
            data[idx].update({'device': d.strip(), 'title': t.strip()})
        elif etype == "type_links":
            s, p = (update.message.text.split(',', 1) if ',' in update.message.text else (update.message.text, "#"))
            data[idx].update({'sensi_link': s.strip(), 'panel_link': p.strip()})
        save_json(data)
        await update.message.reply_text("✅ আপডেট হয়েছে!")
    
    return ConversationHandler.END

def get_json():
    try: return json.loads(base64.b64decode(repo.get_contents("data.json").content).decode())
    except: return []

def save_json(data):
    try:
        c = repo.get_contents("data.json")
        repo.update_file(c.path, "Up", json.dumps(data, indent=2), c.sha)
    except: pass

async def cancel(u, c): await u.message.reply_text("❌"); return ConversationHandler.END

def main():
    keep_alive()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('upload', upload_start)],
        states={
            THUMBNAIL: [MessageHandler(filters.PHOTO, receive_thumbnail)],
            TITLE_DEVICE: [MessageHandler(filters.TEXT, receive_title)],
            SECRET_IMG: [MessageHandler(filters.PHOTO, receive_secret)],
            LINKS: [MessageHandler(filters.TEXT, receive_links)],
        }, fallbacks=[CommandHandler('cancel', cancel)]))
    
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_select, pattern="^type_")],
        states={EDIT_VALUE: [MessageHandler(filters.TEXT, receive_edit_value)]},
        fallbacks=[CommandHandler('cancel', cancel)]))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("manage", manage))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot Running...")
    app.run_polling()

if __name__ == '__main__': main()
