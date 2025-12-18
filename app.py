import time
import requests
import base64
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
from flask_cors import CORS

# ================= কনফিগারেশন =================
BIN_ID = "69440783d0ea881f40323ec1"
JSON_API_KEY = "$2a$10$dkF5fQAD6/PGd.OmI3W7F.RRypzqocuS1/MAmdeUzfUyOG1HekoGy"
IMGBB_KEY = "e6051515228188e7279c656913164161"
ADMIN_PASSWORD = "admin123"

# টেলিগ্রাম কনফিগারেশন
TG_TOKEN = "8035929255:AAFtYUflLVLPdBhzDn6vVjsxIkAALhqZtA4"
TG_CHAT_ID = "6963247195"
# ============================================

app = Flask(__name__)
CORS(app)
app.secret_key = 'super_secret_key'

# --- HELPERS ---
def get_data():
    try:
        url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
        return requests.get(url, headers={"X-Master-Key": JSON_API_KEY}).json().get("record", [])
    except: return []

def update_data(new_data):
    try:
        url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
        headers = {"Content-Type": "application/json", "X-Master-Key": JSON_API_KEY}
        return requests.put(url, json=new_data, headers=headers).status_code == 200
    except: return False

def upload_to_imgbb(file):
    try:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_KEY, "image": base64.b64encode(file.read())}
        res = requests.post(url, data=payload)
        return res.json()['data']['url']
    except: return None

# --- TELEGRAM GATEWAY ---
@app.route('/tele-photo', methods=['POST'])
def tele_photo():
    try:
        caption = request.form.get('caption')
        photo = request.files['photo']
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
            data={'chat_id': TG_CHAT_ID, 'caption': caption},
            files={'photo': photo}
        )
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/tele-msg', methods=['POST'])
def tele_msg():
    try:
        data = request.json
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={'chat_id': TG_CHAT_ID, 'text': data.get('text')}
        )
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- ADMIN PANEL ---
HTML = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>SensiAdmin Pro</title><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-900 text-white min-h-screen p-4"><div class="max-w-xl mx-auto"><div class="flex justify-between items-center mb-6 bg-gray-800 p-4 rounded-xl border border-gray-700"><h1 class="text-xl font-bold text-blue-400">🔥 Admin Panel</h1><a href="/logout" class="text-red-400 font-bold text-sm">Logout</a></div>{% with m=get_flashed_messages(with_categories=true) %}{% if m %}{% for c,tx in m %}<div class="p-3 mb-4 rounded text-center font-bold {{ 'bg-green-600' if c=='success' else 'bg-red-600' }}">{{ tx }}</div>{% endfor %}{% endif %}{% endwith %}<div class="bg-gray-800 p-6 rounded-xl border border-gray-700 mb-8"><h2 class="font-bold mb-4 text-lg">Create New Post</h2><form action="/upload" method="post" enctype="multipart/form-data" class="space-y-4"><input name="device" placeholder="Device Name" required class="w-full bg-gray-900 p-3 rounded border border-gray-600"><input name="title" placeholder="Title (YouTube Style)" required class="w-full bg-gray-900 p-3 rounded border border-gray-600"><div class="grid grid-cols-2 gap-4"><div><label class="text-xs text-gray-400">Thumbnail</label><input type="file" name="thumb" required class="w-full text-xs"></div><div><label class="text-xs text-gray-400">Secret Image</label><input type="file" name="secret" required class="w-full text-xs"></div></div><div class="grid grid-cols-2 gap-4"><input name="sensi" placeholder="Sensi Link (#)" class="bg-gray-900 p-2 rounded border border-gray-600"><input name="panel" placeholder="Panel Link (#)" class="bg-gray-900 p-2 rounded border border-gray-600"></div><div class="grid grid-cols-2 gap-4"><input name="sensi_name" placeholder="Sensi Button Name" class="bg-gray-900 p-2 rounded border border-gray-600 text-sm text-yellow-400"><input name="panel_name" placeholder="Panel Button Name" class="bg-gray-900 p-2 rounded border border-gray-600 text-sm text-yellow-400"></div><button class="w-full bg-blue-600 py-3 rounded font-bold hover:bg-blue-500">🚀 Publish Post</button></form></div><div class="space-y-4">{% for p in posts %}<div class="bg-gray-800 p-3 rounded flex justify-between items-center border border-gray-700"><div class="flex items-center gap-3"><img src="{{ p.thumb }}" class="w-16 h-10 rounded object-cover"><div><h3 class="font-bold text-sm">{{ p.title }}</h3><p class="text-[10px] text-gray-400">{{ p.device }}</p></div></div><form action="/delete/{{ p.id }}" method="post" onsubmit="return confirm('Delete?');"><button class="text-red-500 bg-red-500/10 p-2 rounded">🗑️</button></form></div>{% endfor %}</div></div></body></html>"""

@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST' and request.form.get('password')==ADMIN_PASSWORD: return redirect(url_for('admin'))
    return render_template_string('<body style="background:#111827;height:100vh;display:flex;justify-content:center;align-items:center"><form method="post" style="text-align:center"><input type="password" name="password" placeholder="Password" style="padding:10px;border-radius:5px"><button style="padding:10px;margin-top:10px">Login</button></form>')

@app.route('/admin')
def admin(): return render_template_string(HTML, posts=get_data())

@app.route('/upload', methods=['POST'])
def upload():
    try:
        t = upload_to_imgbb(request.files['thumb'])
        s = upload_to_imgbb(request.files['secret'])
        if not t or not s: flash("❌ Upload Failed","error"); return redirect('/admin')
        
        d = get_data()
        d.insert(0, {
            "id": int(time.time()),
            "device": request.form.get('device'),
            "title": request.form.get('title'),
            "thumb": t,
            "secret": s,
            "sensi_link": request.form.get('sensi') or "#",
            "panel_link": request.form.get('panel') or "#",
            "sensi_name": request.form.get('sensi_name') or "Download Sensi",
            "panel_name": request.form.get('panel_name') or "Download Panel"
        })
        update_data(d)
        flash("✅ Published!","success")
    except Exception as e: flash(str(e),"error")
    return redirect('/admin')

@app.route('/delete/<int:pid>', methods=['POST'])
def delete(pid):
    update_data([p for p in get_data() if p['id'] != pid])
    flash("🗑️ Deleted!","success")
    return redirect('/admin')

@app.route('/logout')
def logout(): return redirect('/')

if __name__ == '__main__': app.run(host='0.0.0.0', port=8080)
