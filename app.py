import os
import json
import base64
import time
from flask import Flask, request, render_template_string, redirect, url_for, flash
from github import Github

# ================= কনফিগারেশন =================
GITHUB_TOKEN = "Ghp_zT7kPcLPdsHwVuoP2NQAPW1p78Bg5v1ihD9N"
REPO_NAME = "sfreezsakib/sensibd"
ADMIN_PASSWORD = "admin123"  # লগইন পাসওয়ার্ড
# ============================================

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# --- GITHUB কানেকশন ---
def get_repo():
    try:
        g = Github(GITHUB_TOKEN)
        return g.get_repo(REPO_NAME)
    except: return None

def get_data():
    repo = get_repo()
    if not repo: return []
    try:
        content = repo.get_contents("data.json")
        return json.loads(base64.b64decode(content.content).decode('utf-8'))
    except: return []

def push_file(file_storage):
    repo = get_repo()
    if not repo: return None
    try:
        filename = f"images/{int(time.time())}_{file_storage.filename}"
        repo.create_file(filename, f"Upload {filename}", file_storage.read())
        return f"https://raw.githubusercontent.com/{REPO_NAME.split('/')[0]}/{REPO_NAME.split('/')[1]}/main/{filename}"
    except: return None

def update_json(new_data):
    repo = get_repo()
    if not repo: return False
    try:
        c = repo.get_contents("data.json")
        repo.update_file(c.path, "Update", json.dumps(new_data, indent=2), c.sha)
        return True
    except: return False

# --- HTML টেমপ্লেট ---
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-slate-900 text-white min-h-screen p-4">
    <div class="max-w-3xl mx-auto">
        <div class="flex justify-between items-center mb-6 bg-slate-800 p-4 rounded-lg shadow-lg">
            <h1 class="text-xl font-bold text-indigo-400">🔥 SensiBD Admin</h1>
            <a href="/logout" class="text-red-400 font-bold text-sm">Logout</a>
        </div>
        
        {% with msgs = get_flashed_messages(with_categories=true) %}
          {% if msgs %}
            {% for cat, msg in msgs %}
              <div class="p-3 mb-4 rounded {{ 'bg-green-600' if cat == 'success' else 'bg-red-600' }}">{{ msg }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="bg-slate-800 p-6 rounded-lg shadow-lg mb-8 border border-slate-700">
            <h2 class="font-bold mb-4 text-lg">New Post</h2>
            <form action="/upload" method="post" enctype="multipart/form-data" class="space-y-3">
                <input type="text" name="device" placeholder="Device Name (e.g. Redmi 10)" required class="w-full bg-slate-900 p-2 rounded border border-slate-600">
                <input type="text" name="title" placeholder="Post Title" required class="w-full bg-slate-900 p-2 rounded border border-slate-600">
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-xs text-gray-400">Thumbnail</label>
                        <input type="file" name="thumb" required class="w-full text-xs">
                    </div>
                    <div>
                        <label class="text-xs text-gray-400">Secret Image</label>
                        <input type="file" name="secret" required class="w-full text-xs">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <input type="text" name="sensi" placeholder="Sensi Link (# if none)" class="bg-slate-900 p-2 rounded border border-slate-600">
                    <input type="text" name="panel" placeholder="Panel Link (# if none)" class="bg-slate-900 p-2 rounded border border-slate-600">
                </div>

                <button class="w-full bg-indigo-600 py-2 rounded font-bold hover:bg-indigo-500">Publish Now</button>
            </form>
        </div>

        <div class="space-y-4">
            <h2 class="font-bold text-lg">Recent Posts</h2>
            {% for post in posts %}
            <div class="bg-slate-800 p-3 rounded flex justify-between items-center border border-slate-700">
                <div class="flex items-center gap-3">
                    <img src="{{ post.thumb }}" class="w-12 h-12 object-cover rounded">
                    <div>
                        <h3 class="font-bold text-sm">{{ post.title }}</h3>
                        <p class="text-xs text-gray-400">{{ post.device }}</p>
                    </div>
                </div>
                <form action="/delete/{{ post.id }}" method="post" onsubmit="return confirm('Delete?');">
                    <button class="text-red-400 hover:text-red-300"><i class="fas fa-trash"></i></button>
                </form>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<body style="background:#0f172a; display:flex; justify-content:center; align-items:center; height:100vh; color:white; font-family:sans-serif;">
    <form method="post" style="text-align:center; padding:20px; background:#1e293b; border-radius:10px;">
        <h3>🔒 Admin Login</h3>
        <input type="password" name="password" placeholder="Password" style="padding:5px; border-radius:5px; border:none;">
        <button style="padding:5px 10px; background:#4f46e5; color:white; border:none; border-radius:5px; cursor:pointer;">Login</button>
    </form>
</body>
"""

# --- ROUTES ---
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
        dev = request.form.get('device')
        tit = request.form.get('title')
        thu = request.files.get('thumb')
        sec = request.files.get('secret')
        sen = request.form.get('sensi') or "#"
        pan = request.form.get('panel') or "#"

        t_url = push_file(thu)
        s_url = push_file(sec)

        if not t_url or not s_url:
            flash("❌ Image Upload Failed!", "error")
            return redirect(url_for('admin'))

        data = get_data()
        data.insert(0, {
            "id": int(time.time()),
            "device": dev, "title": tit,
            "thumb": t_url, "secret": s_url,
            "sensi_link": sen, "panel_link": pan
        })
        
        if update_json(data): flash("✅ Published!", "success")
        else: flash("❌ Database Error!", "error")
    except Exception as e: flash(f"Error: {e}", "error")
    return redirect(url_for('admin'))

@app.route('/delete/<int:pid>', methods=['POST'])
def delete(pid):
    data = [p for p in get_data() if p['id'] != pid]
    if update_json(data): flash("🗑️ Deleted!", "success")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout(): return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
