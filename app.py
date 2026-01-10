import os
import random
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------------- DATABASE ----------------
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.monitoring
sessions = db.sessions

# ---------------- EMAIL ----------------
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_alert_email(to_email):
    msg = EmailMessage()
    msg["Subject"] = "⚠️ Monitoring Alert"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    msg.set_content(
        "Suspicious activity has been detected.\n\n"
        "Your monitored items may be at risk.\n"
        "Please check the system immediately."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)


def trigger_warning():
    session = sessions.find_one({"active": True})


    if session:
        send_alert_email(session["email"])
    
    return "Alert sent"


# ---------------- PAGES ----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/idle_page")
def idle_page():
    return render_template("idle_page.html")


@app.route("/warning")
def warning():
    return render_template("warning.html")


# ---------------- START SESSION ----------------
@app.route("/start-session", methods=["POST"])
def start_session():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    passkey = str(random.randint(10, 99))

    session = {
        "email": email,
        "passkey": passkey,
        "active": True,
        "createdAt": datetime.now(timezone.utc)
    }

    try:
        sessions.insert_one(session)
    except Exception as e:
        print("MongoDB error:", e)
        return jsonify({"error": "Database unavailable"}), 500

    return jsonify({
        "message": "Monitoring started",
        "passkey": passkey
    })


# ---------------- END SESSION ----------------
@app.route("/end-session", methods=["POST"])
def end_session():
    data = request.json
    email = data.get("email")
    passkey = data.get("passkey")

    session = sessions.find_one({
        "email": email,
        "passkey": passkey,
        "active": True
    })

    if not session:
        return jsonify({"error": "Invalid email or passkey"}), 401

    sessions.update_one(
        {"_id": session["_id"]},
        {"$set": {"active": False}}
    )

    return jsonify({"message": "Monitoring ended"})


# ---------------- DEMO ALERT TRIGGER ----------------
@app.route("/trigger-alert")
def trigger_alert():
    trigger_warning()
    return "Alert emails sent"


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
