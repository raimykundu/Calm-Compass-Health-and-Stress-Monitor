import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

# Explicitly look for and load a local .env file if it exists
load_dotenv()

# Configures Flask to look upward precisely into the Vercel architecture layer
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get("APP_SECRET_KEY", "calm-compass-fallback-secret-2026")

# OAuth Configuration setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Safety Trigger Words for Mode 3 (Smart Resource Router) 
CRISIS_KEYWORDS = ["suicide", "harm", "kill", "die", "hurt myself", "end my life", "panic attack", "cannot breathe"]

def get_groq_client():
    """Initializes the Groq Client safely."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

@app.route('/')
def landing():
    """Serves the central landing platform entrance page."""
    return render_template('landing.html')

@app.route('/dashboard')
def home():
    """Serves the primary user interface workspace dashboard."""
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/login')
def login():
    """Initiates the redirection pipeline to the Google OAuth portal."""
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/callback')
def auth_callback():
    """Processes incoming authorization tokens and validates user profiles."""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info:
            session['user'] = user_info
        return redirect(url_for('home'))
    except Exception as e:
        return jsonify({"error": f"Authentication validation failed: {str(e)}"}), 400

@app.route('/logout')
def logout():
    """Clears localized active user identity sessions and returns to landing."""
    session.pop('user', None)
    return redirect(url_for('landing'))

@app.route('/api/chat', methods=['POST'])
def chat_companion():
    """Mode 1: Comfort Companion Chatbot"""
    data = request.json or {}
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"reply": "I'm right here listening. Tell me what's on your mind."}), 400

    safety_triggered = any(keyword in user_message.lower() for keyword in CRISIS_KEYWORDS)

    client = get_groq_client()
    if not client:
        return jsonify({
            "reply": "Groq API Configuration missing. Please verify your Environment Variables.",
            "safety_triggered": safety_triggered
        })

    try:
        system_prompt = (
            "You are an empathetic, compassionate US high school peer counselor. Validate feelings "
            "warmly, avoid sounding robotic, and keep answers concise (under 3 sentences)."
        )
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        ai_reply = completion.choices[0].message.content
        return jsonify({"reply": ai_reply, "safety_triggered": safety_triggered})
        
    except Exception as e:
        return jsonify({"reply": f"Engine error handled: {str(e)}", "safety_triggered": safety_triggered}), 500

@app.route('/api/stress-plan', methods=['POST'])
def stress_planner():
    """Mode 2: Stress Metric & Action Planner"""
    data = request.json or {}
    stress_scale = data.get("stress_scale", 5)
    sleep_hours = data.get("sleep_hours", 7)
    heart_rate = data.get("heart_rate", "")

    client = get_groq_client()
    if not client:
        return jsonify({"plan": "Groq config token is unavailable."})

    vitals_context = f", and a resting heart rate of {heart_rate} bpm" if heart_rate else ""
    
    prompt = (
        f"Generate an immediate, comforting, 3-step markdown cooldown action plan for a student experiencing "
        f"a Level {stress_scale}/10 stress state, who slept only {sleep_hours} hours last night{vitals_context}. "
        f"Include one actionable sensory grounding guide. Keep it short."
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a calming high school wellness coach specialized in immediate stress reduction."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500
        )
        return jsonify({"plan": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"plan": f"Could not construct tactical guide: {str(e)}"}), 500

@app.route('/api/sleep-analysis', methods=['POST'])
def sleep_analyser():
    """🌟 NEW FEATURE: Advanced Sleep Pattern Analytics Architecture"""
    data = request.json or {}
    hours = data.get("hours", 7)
    quality = data.get("quality", 70)  # Sleep Quality Percentage
    consistency = data.get("consistency", "variable") # Stable, Variable, Chaotic

    client = get_groq_client()
    if not client:
        return jsonify({"analysis": "Groq API environment link unavailable. Check config."}), 500

    prompt = (
        f"You are a specialized adolescent sleep coach analyzing wearable health data profile graphs.\n"
        f"Student Metrics Profile:\n"
        f"- Total Rest Duration: {hours} hours\n"
        f"- Deep/REM Quality Index: {quality}%\n"
        f"- Circadian Bedtime Schedule Consistency: {consistency}\n\n"
        f"Provide a 3-sentence maximum breakdown pinpointing exactly how their sleep architecture impacts their high-school daytime stress levels. "
        f"Provide one clear, practical adjustment suggestion (e.g., blue-light rules or caffeine windows) to optimize recovery."
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a brief, encouraging health tech coach focusing on circadian clock mechanics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )
        return jsonify({"analysis": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"analysis": f"Sleep metrics analytics processing error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)