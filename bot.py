import os
import json
import base64
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from github import Github

# ============ CREDENTIALS (আপনার তথ্য বসানো হয়েছে) ============
TELEGRAM_TOKEN = "8429248919:AAF403QR9g7FPxNDeLdiIIBBROu25Fbfit8"
GITHUB_TOKEN = "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"
REPO_NAME = "sfreezsakib/sensibd"
# =============================================================

# GitHub Connection
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# States
THUMBNAIL, TITLE_DEVICE, SECRET_IMG, LINKS = range(4)
EDIT_SELECT, EDIT_VALUE = range(4, 6)

temp_data = {}
edit_cache = {}

# --- UPLOAD COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **SensiBD Admin Panel**\n\n"
        "🔹 `/upload` - নতুন সেন্সি বা প্যানেল আপলোড\n"
        "🔹 `/manage` - আগের পোস্ট এডিট বা ডিলিট করুন"
    )

async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1️⃣ পোস্টের **Thumbnail Image** পাঠান।")
    return THUMBNAIL

async def receive_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return THUMBNAIL
    photo = await update.message.photo[-1].get_file()
    fname = f"images/thumb_{int(time.time())}.jpg"
    await photo.download_to_memory()
    
    try:
        repo.create_file(fname, "Add thumb", await (await photo.download_as_bytearray()))
        temp_data['thumb'] = f"https://raw.githubusercontent.com/{REPO_NAME.split('/')[0]}/{REPO_NAME.split('/')[1]}/main/{fname}"
        await update.message.reply_text("✅ থাম্বনেইল সেভ হয়েছে।\n\n2️⃣ লিখুন: `Device Name | Title`\nউদাহরণ: `Realme 8 | Headshot Config`")
        return TITLE_DEVICE
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if '|' not in text: 
        await update.message.reply_text("❌ ভুল ফরম্যাট! মাঝখানে '|' চিহ্ন দিন।")
        return TITLE_DEVICE
    dev, tit = text.split('|', 1)
    temp_data.update({'device': dev.strip(), 'title': tit.strip(), 'id': int(time.time())})
    await update.message.reply_text("✅ টাইটেল সেট হয়েছে।\n\n3️⃣ এবার **Secret/Sensi Image** (লক করা ছবি) পাঠান।")
    return SECRET_IMG

async def receive_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return SECRET_IMG
    photo = await update.message.photo[-1].get_file()
    fname = f"images/secret_{int(time.time())}.jpg"
    
    try:
        repo.create_file(fname, "Add secret", await (await photo.download_as_bytearray()))
        temp_data['secret'] = f"https://raw.githubusercontent.com/{REPO_NAME.split('/')[0]}/{REPO_NAME.split('/')[1]}/main/{fname}"
        await update.message.reply_text("✅ সিক্রেট ইমেজ সেভ হয়েছে।\n\n4️⃣ লিংক দিন: `Sensi Link, Panel Link`\n(লিংক না থাকলে # দিন, কমা দিয়ে আলাদা করুন)")
        return LINKS
    except: return ConversationHandler.END

async def receive_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    sensi, panel = (text.split(',', 1) if ',' in text else (text, "#"))
    temp_data.update({'sensi_link': sensi.strip(), 'panel_link': panel.strip()})
    
    # Save to JSON
    update_json(temp_data.copy(), "add")
    await update.message.reply_text(f"🎉 **পোস্ট পাবলিশ হয়েছে!**\nTitle: {temp_data['title']}")
    temp_data.clear()
    return ConversationHandler.END

# --- MANAGE (EDIT/DELETE) COMMANDS ---
async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_json()
    if not data:
        await update.message.reply_text("📭 কোনো পোস্ট নেই।")
        return

    # Show last 5 posts
    await update.message.reply_text("👇 **Last 5 Posts:**")
    for post in data[:5]: 
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{post['id']}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"del_{post['id']}")
            ]
        ]
        await update.message.reply_text(
            f"📱 **{post['device']}**\n📌 {post['title']}", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if "_" not in query.data: return
    action, pid = query.data.split('_', 1)
    
    if action == "type": return # Handled by conversation

    pid = int(pid)

    if action == "del":
        data = get_json()
        new_data = [p for p in data if p['id'] != pid]
        save_json(new_data)
        await query.edit_message_text(f"🗑️ পোস্ট ডিলিট করা হয়েছে।")

    elif action == "edit":
        edit_cache['id'] = pid
        keyboard = [
            [InlineKeyboardButton("Title & Device", callback_data="type_title")],
            [InlineKeyboardButton("Links", callback_data="type_links")],
            [InlineKeyboardButton("Thumbnail (Photo)", callback_data="type_thumb")]
        ]
        await query.edit_message_text("কি এডিট করতে চান?", reply_markup=InlineKeyboardMarkup(keyboard))
        return EDIT_SELECT

async def edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    edit_cache['type'] = query.data
    
    msg_map = {
        "type_title": "নতুন `Device | Title` লিখে পাঠান:",
        "type_links": "নতুন `Sensi Link, Panel Link` পাঠান:",
        "type_thumb": "নতুন Thumbnail ছবিটি পাঠান:"
    }
    await query.message.reply_text(msg_map.get(query.data, "Send Data"))
    return EDIT_VALUE

async def receive_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = edit_cache.get('id')
    etype = edit_cache.get('type')
    data = get_json()
    
    idx = next((i for i, item in enumerate(data) if item["id"] == pid), -1)
    if idx == -1:
        await update.message.reply_text("❌ পোস্ট পাওয়া যায়নি।")
        return ConversationHandler.END

    if etype == "type_thumb":
        if update.message.photo:
            photo = await update.message.photo[-1].get_file()
            fname = f"images/thumb_{pid}_{int(time.time())}.jpg"
            repo.create_file(fname, "Update thumb", await (await photo.download_as_bytearray()))
            data[idx]['thumb'] = f"https://raw.githubusercontent.com/{REPO_NAME.split('/')[0]}/{REPO_NAME.split('/')[1]}/main/{fname}"
            await update.message.reply_text("✅ থাম্বনেইল আপডেট হয়েছে!")
        else:
            await update.message.reply_text("❌ ছবি পাঠাননি।")
            return ConversationHandler.END

    elif etype == "type_title":
        text = update.message.text
        if '|' in text:
            d, t = text.split('|', 1)
            data[idx]['device'] = d.strip()
            data[idx]['title'] = t.strip()
            await update.message.reply_text("✅ টাইটেল আপডেট হয়েছে!")
        else: return ConversationHandler.END

    elif etype == "type_links":
        text = update.message.text
        s, p = (text.split(',', 1) if ',' in text else (text, "#"))
        data[idx]['sensi_link'] = s.strip()
        data[idx]['panel_link'] = p.strip()
        await update.message.reply_text("✅ লিংক আপডেট হয়েছে!")

    save_json(data)
    edit_cache.clear()
    return ConversationHandler.END

# --- HELPERS ---
def get_json():
    try:
        content = repo.get_contents("data.json")
        return json.loads(base64.b64decode(content.content).decode('utf-8'))
    except: return []

def save_json(data):
    try:
        content = repo.get_contents("data.json")
        repo.update_file(content.path, "Update data", json.dumps(data, indent=2), content.sha)
    except: pass

def update_json(item, mode):
    data = get_json()
    if mode == "add": data.insert(0, item)
    save_json(data)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ বাতিল।")
    return ConversationHandler.END

# --- MAIN ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    upload_conv = ConversationHandler(
        entry_points=[CommandHandler('upload', upload_start)],
        states={
            THUMBNAIL: [MessageHandler(filters.PHOTO, receive_thumbnail)],
            TITLE_DEVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            SECRET_IMG: [MessageHandler(filters.PHOTO, receive_secret)],
            LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_links)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_select, pattern="^type_")],
        states={EDIT_VALUE: [MessageHandler(filters.TEXT | filters.PHOTO, receive_edit_value)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(upload_conv)
    app.add_handler(edit_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("manage", manage))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot Started...")
    app.run_polling()

if __name__ == '__main__':
    main()
