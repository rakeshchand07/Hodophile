"""
Hodophile - Premium AI Travel Planner
Flask Backend Application
"""
import os, json, hashlib, sqlite3, requests
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, send_from_directory)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')

load_dotenv(env_path)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hodophile-dev-secret-2024')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
UPLOAD_MEMORIES = os.path.join(BASE_DIR, 'uploads', 'memories')
UPLOAD_PROFILES = os.path.join(BASE_DIR, 'uploads', 'profiles')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(UPLOAD_MEMORIES, exist_ok=True)
os.makedirs(UPLOAD_PROFILES, exist_ok=True)

GEMINI_API_KEY  = os.getenv('GEMINI_API_KEY', '')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
IMAGE_API_KEY   = os.getenv('IMAGE_API_KEY', '')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_if_needed():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
            photo TEXT DEFAULT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            destination TEXT NOT NULL, days INTEGER NOT NULL, budget REAL NOT NULL,
            travelers INTEGER NOT NULL DEFAULT 1, vibe TEXT NOT NULL DEFAULT 'Adventure',
            month TEXT NOT NULL DEFAULT 'January', itinerary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL, caption TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
        conn.commit()
        conn.close()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    u = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    db.close()
    return u

def call_gemini(prompt):
    if not GEMINI_API_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        r = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}]}, timeout=30)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return None
print("LOADED WEATHER KEY:", os.getenv("WEATHER_API_KEY"))
def get_weather_data(city):
    print("\n==== WEATHER DEBUG START ====")
    print("CITY:", city)
    print("API KEY:", WEATHER_API_KEY)

    if not WEATHER_API_KEY:
        print("❌ API KEY MISSING")
        return None

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        print("URL:", url)

        r = requests.get(url, timeout=10)

        print("STATUS CODE:", r.status_code)
        print("RAW RESPONSE:", r.text)

        if r.status_code != 200:
            print("❌ API FAILED")
            return None

        data = r.json()

        # Extra safety check
        if 'main' not in data or 'weather' not in data:
            print("❌ INVALID RESPONSE STRUCTURE")
            return None

        print("✅ WEATHER DATA RECEIVED")
        print("==== WEATHER DEBUG END ====\n")

        return data

    except Exception as e:
        print("❌ EXCEPTION:", str(e))
        return None

def get_places(query):
    if not GOOGLE_MAPS_KEY:
        return []
    try:
        r = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json",
                         params={"query": query, "key": GOOGLE_MAPS_KEY}, timeout=10)
        return r.json().get('results', [])[:5]
    except:
        return []

def get_unsplash_images(query, count=6):
    if not IMAGE_API_KEY:
        return []
    try:
        r = requests.get("https://api.unsplash.com/search/photos",
                         params={"query": query, "per_page": count, "client_id": IMAGE_API_KEY}, timeout=10)
        return [x['urls']['regular'] for x in r.json().get('results', [])]
    except:
        return []

def fallback_plan(dest, days, budget, travelers, vibe, month):
    days_int = int(days)
    budget_int = int(float(budget))
    travelers_int = int(travelers)
    acts = [
        ("Arrival & First Impressions 🌅","Arrive and settle in. Explore nearby area.","Visit main market and local bazaar.","Welcome dinner at a celebrated local restaurant."),
        ("Cultural Deep Dive 🏛","Visit the iconic historical monument or temple.","Local museum, art gallery or heritage walk.","Traditional cultural show or street food trail."),
        ("Nature & Adventure 🌿","Scenic nature walk, hill trek or beach visit.","Adventure activity or panoramic viewpoint.","Sunset photography followed by a rooftop dinner."),
        ("Hidden Gems 💎","Off-the-beaten-path neighbourhood exploration.","Local craft shopping and workshop experience.","Fine dining celebrating authentic local cuisine."),
        ("Leisure & Departure 🎒","Relaxed final breakfast. Visit any missed spots.","Last-minute souvenir shopping.","Farewell dinner and departure preparations."),
    ]
    days_text = "\n".join([f"Day {i+1}: {acts[i%len(acts)][0]}\n  Morning   → {acts[i%len(acts)][1]}\n  Afternoon → {acts[i%len(acts)][2]}\n  Evening   → {acts[i%len(acts)][3]}" for i in range(days_int)])
    return f"""OVERVIEW:
{dest} is a magnificent destination for {vibe.lower()} travellers in {month}. With ₹{budget_int:,} for {travelers_int} traveller(s) over {days_int} days, you'll enjoy culture, cuisine and discovery.

DAY-WISE ITINERARY:
{days_text}

MUST-VISIT ATTRACTIONS:
• The Central Landmark — the iconic symbol every visitor must see
• The Natural Reserve — breathtaking landscapes unique to this region
• The Old Quarter — historic streets with centuries of stories
• The Sacred Temple — spiritual heart of {dest}
• The Panoramic Viewpoint — best sunset views in the area

LOCAL FOOD EXPERIENCES:
• Signature regional curry — a must-try dish perfected over generations
• Street food market — authentic flavours from roadside vendors
• Local sweet shop — beloved desserts with century-old recipes
• Fresh seafood or regional specialty — farm-to-table at its finest

BUDGET OPTIMIZATION TIPS:
• Book accommodation 2–3 weeks ahead for 20–35% savings
• Use local transport (auto, bus) instead of private taxis
• Eat at thali restaurants for authentic meals at ₹100–200/plate
• Visit monuments early morning to avoid crowds and heat

SAFETY & TRAVEL ADVISORIES:
• Carry copies of all documents (physical + cloud backup)
• Use only registered taxis or ride-hailing apps at night
• Stay hydrated and carry a small first-aid kit

PACKING ESSENTIALS FOR {month.upper()}:
Sunscreen SPF 50, Walking shoes, Camera, Power bank, Rain jacket, Travel adapter, Water bottle, Hand sanitizer, First aid kit, Daypack, Sunglasses, Light scarf"""

@app.route('/')
def index():
    init_db_if_needed()
    return render_template('index.html', user=current_user())

@app.route('/signup', methods=['GET','POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        confirm = request.form.get('confirm_password','')
        if not name or not email or not password:
            flash('All fields are required.','error'); return render_template('signup.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.','error'); return render_template('signup.html')
        if password != confirm:
            flash('Passwords do not match.','error'); return render_template('signup.html')
        db = get_db()
        if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
            db.close(); flash('Email already registered.','error'); return render_template('signup.html')
        db.execute('INSERT INTO users (name,email,password) VALUES (?,?,?)',(name,email,hash_password(password)))
        db.commit()
        uid = db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()['id']
        db.close()
        session['user_id'] = uid; session['user_name'] = name
        flash(f'Welcome to Hodophile, {name}! ✦','success')
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        db = get_db()
        u = db.execute('SELECT * FROM users WHERE email=? AND password=?',(email,hash_password(password))).fetchone()
        db.close()
        if u:
            session['user_id'] = u['id']; session['user_name'] = u['name']
            flash(f'Welcome back, {u["name"]}! ✈','success')
            return redirect(url_for('index'))
        flash('Invalid email or password.','error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); flash('Logged out. Safe travels! 🌍','info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    u = current_user()
    db = get_db()
    trips = db.execute('SELECT * FROM trips WHERE user_id=? ORDER BY created_at DESC',(u['id'],)).fetchall()
    mems = db.execute('SELECT * FROM memories WHERE user_id=? ORDER BY created_at DESC',(u['id'],)).fetchall()
    db.close()
    return render_template('profile.html', user=u, trips=trips, memories=mems)

@app.route('/edit-profile', methods=['GET','POST'])
@login_required
def edit_profile():
    u = current_user()
    if request.method == 'POST':
        name = request.form.get('name','').strip() or u['name']
        email = request.form.get('email','').strip().lower() or u['email']
        new_pass = request.form.get('new_password','')
        photo_path = u['photo']
        if 'photo' in request.files:
            f = request.files['photo']
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit('.',1)[1].lower()
                fn = secure_filename(f"user_{u['id']}_{int(datetime.now().timestamp())}.{ext}")
                f.save(os.path.join(UPLOAD_PROFILES, fn))
                photo_path = fn
        db = get_db()
        if new_pass and len(new_pass) >= 6:
            db.execute('UPDATE users SET name=?,email=?,password=?,photo=? WHERE id=?',(name,email,hash_password(new_pass),photo_path,u['id']))
        else:
            db.execute('UPDATE users SET name=?,email=?,photo=? WHERE id=?',(name,email,photo_path,u['id']))
        db.commit(); db.close()
        session['user_name'] = name
        flash('Profile updated! ✓','success'); return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=u)

@app.route('/uploads/profiles/<filename>')
def profile_image(filename):
    return send_from_directory(UPLOAD_PROFILES, filename)

@app.route('/plan-trip', methods=['GET','POST'])
@login_required
def plan_trip():
    u = current_user()
    if request.method == 'POST':
        dest = request.form.get('destination','').strip()
        days = request.form.get('days', 5)
        budget = request.form.get('budget', 50000)
        travelers = request.form.get('travelers', 2)
        vibe = request.form.get('vibe','Adventure')
        month = request.form.get('month','January')
        if not dest:
            flash('Please enter a destination.','error'); return render_template('plan_trip.html', user=u)
        prompt = f"""You are Hodophile, a world-class luxury AI travel planner. Create a comprehensive, inspiring travel plan for:
Destination: {dest}
Duration: {days} days | Budget: ₹{int(float(budget)):,} for {travelers} traveller(s)
Travel Style: {vibe} | Month: {month}

Use EXACT headers:
OVERVIEW:
[3 vivid inspiring sentences]

DAY-WISE ITINERARY:
Day 1: [Title] [Emoji]
  Morning   → [activity]
  Afternoon → [activity]
  Evening   → [activity/dinner]
[continue for all {days} days]

MUST-VISIT ATTRACTIONS:
• [Attraction] — [why unmissable]
[5 attractions total]

LOCAL FOOD EXPERIENCES:
• [Food/Place] — [description]
[4 items total]

BUDGET OPTIMIZATION TIPS:
• [tip]
[4 tips total]

SAFETY & TRAVEL ADVISORIES:
• [tip]
[3 tips total]

PACKING ESSENTIALS FOR {month.upper()}:
[12 items, comma-separated]

Use real place names. Use emojis. Make it feel like luxury travel magazine."""
        itinerary = call_gemini(prompt) or fallback_plan(dest,days,budget,travelers,vibe,month)
        budget_val = float(budget)
        budget_breakdown = {"Stay":round(budget_val*0.35,0),"Food":round(budget_val*0.25,0),"Transport":round(budget_val*0.20,0),"Activities":round(budget_val*0.15,0),"Misc":round(budget_val*0.05,0)}
        hotels = get_places(f"hotels in {dest}")
        restaurants = get_places(f"top restaurants in {dest}")
        attractions = get_places(f"tourist attractions in {dest}")
        images = get_unsplash_images(dest, 6)
        map_url = f"https://www.google.com/maps/search/{dest.replace(' ','+')}"
        packing = []
        if "PACKING ESSENTIALS" in itinerary:
            sec = itinerary.split("PACKING ESSENTIALS")[1]
            line = [l for l in sec.split('\n') if l.strip()]
            if len(line) > 1:
                packing = [p.strip() for p in line[1].split(',') if p.strip()][:12]
        if not packing:
            packing = ["Sunscreen SPF 50","Walking shoes","Camera","Power bank","Rain jacket","Travel adapter","Water bottle","Hand sanitizer","First aid kit","Daypack"]
        return render_template('result.html', user=u, destination=dest, days=days, budget=budget_val,
            budget_breakdown=budget_breakdown, travelers=travelers, vibe=vibe, month=month,
            itinerary=itinerary, hotels=hotels, restaurants=restaurants, attractions=attractions,
            images=images, packing=packing, map_url=map_url)
    return render_template('plan_trip.html', user=u)

@app.route('/save-trip', methods=['POST'])
@login_required
def save_trip():
    u = current_user(); data = request.get_json(); db = get_db()
    db.execute('INSERT INTO trips (user_id,destination,days,budget,travelers,vibe,month,itinerary) VALUES (?,?,?,?,?,?,?,?)',
               (u['id'],data.get('destination'),data.get('days'),data.get('budget'),data.get('travelers',1),data.get('vibe','Adventure'),data.get('month','January'),data.get('itinerary')))
    db.commit(); db.close()
    return jsonify({'status':'saved','message':'Trip saved!'})

@app.route('/delete-trip/<int:tid>', methods=['POST'])
@login_required
def delete_trip(tid):
    u = current_user(); db = get_db()
    db.execute('DELETE FROM trips WHERE id=? AND user_id=?',(tid,u['id'])); db.commit(); db.close()
    flash('Trip deleted.','info'); return redirect(url_for('saved_trips'))

@app.route('/saved-trips')
@login_required
def saved_trips():
    u = current_user(); db = get_db()
    trips = db.execute('SELECT * FROM trips WHERE user_id=? ORDER BY created_at DESC',(u['id'],)).fetchall(); db.close()
    return render_template('saved_trips.html', user=u, trips=trips)

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html', user=current_user())

@app.route('/api/chat', methods=['POST'])
def api_chat():
    msg = (request.get_json() or {}).get('message','').strip()
    if not msg:
        return jsonify({'reply':'Please type a message!'})
    prompt = f"""You are Hodophile AI, a premium luxury travel assistant. Be warm, enthusiastic, specific. Use real place names. Practical tips. Inspiring ideas. Under 250 words. Use emojis.\n\nUser: {msg}\n\nResponse:"""
    reply = call_gemini(prompt) or get_chat_fallback(msg)
    return jsonify({'reply': reply})

def get_chat_fallback(msg):
    ml = msg.lower()
    if any(w in ml for w in ['summer','june','may','hot']):
        return "☀️ Top summer destinations in India:\n\n🏔 Hills: Manali, Shimla, Darjeeling, Coorg, Munnar, Ooty\n🏔 Adventure: Ladakh (Jun–Sep peak), Spiti Valley\n🌊 Coastal: Andaman Islands\n\nInternational: Switzerland, Canada, Scandinavia\n\nPro tip: Book hill-station hotels 3+ weeks ahead — summer fills fast! 🌿"
    if any(w in ml for w in ['budget','cheap','affordable']):
        return "💰 Smart budget travel:\n\n• Travel shoulder season for 30–40% savings\n• Overnight trains save transport + accommodation cost\n• Eat at local dhabas — ₹80–150/meal\n• Stay in OYO/hostels — ₹400–800/night\n• IRCTC trains are the best value for long distances\n\nWhich destination? I'll give specific numbers! 🎯"
    if any(w in ml for w in ['pack','luggage','carry','bring']):
        return "🎒 Packing essentials:\n\n📋 Documents: ID, tickets, insurance, bookings\n👕 Clothes: 5 tops, 4 bottoms, 3 underlayers, 1 jacket\n💊 Health: Sunscreen, sanitizer, ORS, paracetamol, band-aids\n⚡ Tech: 20000mAh power bank, adapter, earphones\n\nGolden rule: Pack 30% less than you think you need! 😄"
    if any(w in ml for w in ['honeymoon','romantic','couple']):
        return "💑 Romantic destinations:\n\n🇮🇳 India: Andaman Islands, Kashmir, Coorg, Udaipur, Alleppey\n🌍 International: Bali, Maldives, Sri Lanka, Paris, Santorini\n\nWhat's your budget? I'll suggest the perfect match! 💕"
    if any(w in ml for w in ['solo','alone']):
        return "🌸 Solo travel — you've got this!\n\n🇮🇳 Best: Rishikesh, Hampi, Goa, Spiti, Varanasi\n\n✅ Safety tips:\n• Share live location with family daily\n• Stay in hostels — instant travel buddies\n• Use Ola/Uber only, avoid unmarked cabs at night\n• Trust your instincts! 🌟"
    return "✈️ I'm here to make your travel dreams real!\n\nI can help with:\n🗺 Destination recommendations\n📅 Day-wise itineraries\n💰 Budget breakdowns\n🎒 Packing lists\n🛡 Safety advisories\n🍽 Food suggestions\n\nWhere do you dream of going? 🌏"

@app.route('/weather')
def weather():
    return render_template('weather.html', user=current_user())

@app.route('/api/weather')
def api_weather():
    city = request.args.get('city','').strip()
    if not city:
        return jsonify({'error':'City required'}), 400
    data = get_weather_data(city)
    if not data:
        return jsonify({'city':city,'temp':24,'feels_like':26,'description':'Partly Cloudy','humidity':65,'wind_speed':12,'icon':'02d','fallback':True})
    return jsonify({'city':data['name'],'country':data['sys']['country'],'temp':round(data['main']['temp']),
        'feels_like':round(data['main']['feels_like']),'description':data['weather'][0]['description'].title(),
        'humidity':data['main']['humidity'],'wind_speed':round(data['wind']['speed']*3.6,1),
        'icon':data['weather'][0]['icon'],'visibility':round(data.get('visibility',10000)/1000,1)})

@app.route('/memories')
@login_required
def memories():
    u = current_user(); db = get_db()
    mems = db.execute('SELECT * FROM memories WHERE user_id=? ORDER BY created_at DESC',(u['id'],)).fetchall(); db.close()
    return render_template('memories.html', user=u, memories=mems)

@app.route('/upload-memory', methods=['POST'])
@login_required
def upload_memory():
    u = current_user()
    if 'file' not in request.files:
        flash('No file selected.','error'); return redirect(url_for('memories'))
    for f in request.files.getlist('file'):
        if f and f.filename and allowed_file(f.filename):
            ext = f.filename.rsplit('.',1)[1].lower()
            fn = secure_filename(f"mem_{u['id']}_{int(datetime.now().timestamp())}_{f.filename}")
            f.save(os.path.join(UPLOAD_MEMORIES, fn))
            db = get_db()
            db.execute('INSERT INTO memories (user_id,file_name,caption) VALUES (?,?,?)',(u['id'],fn,request.form.get('caption','')))
            db.commit(); db.close()
    flash('Memory uploaded! 📸','success'); return redirect(url_for('memories'))

@app.route('/delete-memory/<int:mid>', methods=['POST'])
@login_required
def delete_memory(mid):
    u = current_user(); db = get_db()
    m = db.execute('SELECT * FROM memories WHERE id=? AND user_id=?',(mid,u['id'])).fetchone()
    if m:
        try: os.remove(os.path.join(UPLOAD_MEMORIES, m['file_name']))
        except: pass
        db.execute('DELETE FROM memories WHERE id=?',(mid,)); db.commit()
    db.close(); flash('Memory removed.','info'); return redirect(url_for('memories'))

@app.route('/uploads/memories/<filename>')
def memory_image(filename):
    return send_from_directory(UPLOAD_MEMORIES, filename)

@app.context_processor
def inject_globals():
    return {'current_year': datetime.now().year, 'user': current_user(), 'google_maps_key': GOOGLE_MAPS_KEY}

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', user=current_user()), 404

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Max 10MB.','error'); return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    init_db_if_needed()
    app.run(debug=True, port=5000)
