import time
import requests
from flask import Flask, request, render_template_string, redirect, url_for, flash

# ================= কনফিগারেশন =================
# আপনার দেওয়া তথ্য বসানো হয়েছে
BIN_ID = "69440783d0ea881f40323ec1"
API_KEY = "$2a$10$dkF5fQAD6/PGd.OmI3W7F.RRypzqocuS1/MAmdeUzfUyOG1HekoGy"

ADMIN_PASSWORD = "admin123"  # পাসওয়ার্ড
# ============================================

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# --- JSONBIN কানেকশন ---
def get_data():
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    headers = {"X-Master-Key": API_KEY}
    try:
        resp = requests.get(url, headers=headers)
        return resp.json().get("record", [])
    except: return []

def update_data(new_data):
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": API_KEY
    }
    try:
        req = requests.put(url, json=new_data, headers=headers)
        return req.status_code == 200
    except: return False

# --- HTML টেমপ্লেট ---
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sensi Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-900 text-white min-h-screen p-4">
    <div class="max-w-2xl mx-auto">
        <div class="flex justify-between items-center mb-6 bg-gray-800 p-4 rounded-xl shadow-lg border border-gray-700">
            <h1 class="text-xl font-bold text-green-400">⚡ Admin Panel</h1>
            <a href="/logout" class="text-red-400 font-bold text-sm">Logout</a>
        </div>
        
        {% with msgs = get_flashed_messages(with_categories=true) %}
          {% if msgs %}
            {% for cat, msg in msgs %}
              <div class="p-3 mb-4 rounded text-center font-bold {{ 'bg-green-600' if cat == 'success' else 'bg-red-600' }}">{{ msg }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="bg-gray-800 p-6 rounded-xl shadow-lg mb-8 border border-gray-700">
            <h2 class="font-bold mb-4 text-lg text-indigo-300">New Post</h2>
            <form action="/upload" method="post" class="space-y-4">
                <input type="text" name="device" placeholder="Device Name" required class="w-full bg-gray-900 p-3 rounded border border-gray-600 outline-none">
                <input type="text" name="title" placeholder="Title" required class="w-full bg-gray-900 p-3 rounded border border-gray-600 outline-none">
                
                <div class="grid md:grid-cols-2 gap-4">
                    <input type="text" name="thumb" placeholder="Thumbnail Link (Direct Link)" required class="w-full bg-gray-900 p-3 rounded border border-gray-600 text-sm">
                    <input type="text" name="secret" placeholder="Secret Image Link (Direct Link)" required class="w-full bg-gray-900 p-3 rounded border border-gray-600 text-sm">
                </div>

                <div class="grid md:grid-cols-2 gap-4">
                    <input type="text" name="sensi" placeholder="Sensi Link (#)" class="bg-gray-900 p-3 rounded border border-gray-600 text-sm">
                    <input type="text" name="panel" placeholder="Panel Link (#)" class="bg-gray-900 p-3 rounded border border-gray-600 text-sm">
                </div>

                <button class="w-full bg-green-600 py-3 rounded font-bold hover:bg-green-500 transition">🚀 Publish Post</button>
            </form>
        </div>

        <div class="space-y-4">
            <h2 class="font-bold text-lg">Live Posts</h2>
            {% for post in posts %}
            <div class="bg-gray-800 p-4 rounded-xl flex justify-between items-center border border-gray-700">
                <div class="flex items-center gap-4">
                    <img src="{{ post.thumb }}" class="w-16 h-16 object-cover rounded bg-gray-900" onerror="this.src='https://placehold.co/100x100?text=Error'">
                    <div>
                        <h3 class="font-bold text-sm">{{ post.title }}</h3>
                        <p class="text-xs text-gray-400">{{ post.device }}</p>
                    </div>
                </div>
                <form action="/delete/{{ post.id }}" method="post" onsubmit="return confirm('Delete?');">
                    <button class="bg-red-500/20 text-red-500 p-2 rounded hover:bg-red-500 hover:text-white"><i class="fas fa-trash"></i></button>
                </form>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<body style="background:#111827; display:flex; justify-content:center; align-items:center; height:100vh; color:white; font-family:sans-serif;">
    <form method="post" style="text-align:center; padding:2rem; background:#1f2937; border-radius:1rem; border:1px solid #374151;">
        <h3 style="margin-bottom:1.5rem; color:#4ade80;">Login</h3>
        <input type="password" name="password" placeholder="Password" style="padding:10px; border-radius:5px; border:none; background:#111827; color:white; outline:none;">
        <br><br>
        <button style="padding:10px 20px; background:#16a34a; color:white; border:none; border-radius:5px; font-weight:bold;">Enter</button>
    </form>
</body>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            return redirect(url_for('admin'))
    return render_template_string(LOGIN_HTML)

@app.route('/admin')
def admin():
    return render_template_string(HTML, posts=get_data())

@app.route('/upload', methods=['POST'])
def upload():
    try:
        new_post = {
            "id": int(time.time()),
            "device": request.form.get('device'),
            "title": request.form.get('title'),
            "thumb": request.form.get('thumb'),
            "secret": request.form.get('secret'),
            "sensi_link": request.form.get('sensi') or "#",
            "panel_link": request.form.get('panel') or "#"
        }
        data = get_data()
        data.insert(0, new_post)
        
        if update_data(data): flash("✅ Published!", "success")
        else: flash("❌ Error saving to JSONBin", "error")
    except Exception as e: flash(f"Error: {e}", "error")
    return redirect(url_for('admin'))

@app.route('/delete/<int:pid>', methods=['POST'])
def delete(pid):
    data = [p for p in get_data() if p['id'] != pid]
    if update_data(data): flash("🗑️ Deleted!", "success")
    else: flash("❌ Delete Failed", "error")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout(): return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
