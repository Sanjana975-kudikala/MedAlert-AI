from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import pickle
import numpy as np
import os
import requests
from math import radians, cos, sin, asin, sqrt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================= APP SETUP =================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ================= ENV VARIABLES =================
MONGO_URI = os.getenv("MONGO_URI")
hf_token = os.getenv("HF_TOKEN")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI not found in environment variables")

if not hf_token:
    print("⚠ WARNING: HF_TOKEN not found")

# ================= MONGODB CONNECTION =================
client = MongoClient(MONGO_URI)
db = client["medalert"]
users_collection = db["users"]

# ================= AUTH DECORATOR =================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("loginPage"))
        return f(*args, **kwargs)
    return wrapper

# ================= MODEL LOADING =================
def load_model(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            model, scaler = pickle.load(f)
            return {"model": model, "scaler": scaler}
    return None

MODELS = {
    "Diabetes": load_model("models/diabetes.pkl"),
    "Breast Cancer": load_model("models/breast_cancer.pkl"),
    "Heart Disease": load_model("models/heart.pkl"),
    "Kidney Disease": load_model("models/kidney.pkl"),
    "Liver Disease": load_model("models/liver.pkl"),
}

# ================= DISEASE DETECTION =================
def detect_disease(form):
    keys = form.keys()
    if "pregnancies" in keys:
        return "Diabetes"
    if "radius_mean" in keys:
        return "Breast Cancer"
    if "systolic" in keys:
        return "Heart Disease"
    if "blood_urea" in keys:
        return "Kidney Disease"
    if "total_bilirubin" in keys:
        return "Liver Disease"
    return None

# ================= PREDICTION LOGIC =================
def predict_risk(form):
    disease = detect_disease(form)
    bundle = MODELS.get(disease)
    if not bundle:
        raise ValueError("Model not loaded")

    model = bundle["model"]
    scaler = bundle["scaler"]

    # ===== DIABETES =====
    if disease == "Diabetes":
        fbg = float(form["fbg"])
        hba1c = float(form["hba1c"])
        rbs = float(form["rbs"])
        bp = form["blood_pressure"]
        systolic = float(bp.split("/")[0])
        bmi = float(form["bmi"])
        age = float(form["age"])
        family_history = float(form["family_history"])
        pregnancies = float(form["pregnancies"])
        values = np.array([[fbg, hba1c, rbs, systolic, bmi, age, family_history, pregnancies]])

    # ===== HEART DISEASE =====
    elif disease == "Heart Disease":
        values = np.array([[
            float(form["age"]),
            float(form["systolic"]),
            float(form["diastolic"]),
            float(form["cholesterol"]),
            float(form["hdl"]),
            float(form["ldl"]),
            float(form["triglycerides"]),
            float(form["blood_sugar"]),
            float(form["bmi"]),
            float(form["hr"]),
            float(form["sex"]),
            float(form["family_history"]),
            float(form["smoking"]),
            float(form["diabetes"]),
            float(form["exercise_cp"])
        ]])

    # ===== OTHER DISEASES =====
    else:
        values = np.array([float(v) for v in form.values()]).reshape(1, -1)

    # ===== SCALE + PREDICT =====
    values_scaled = scaler.transform(values)
    probability = model.predict_proba(values_scaled)[0][1]

    if probability >= 0.7:
        level = "HIGH RISK"
    elif probability >= 0.5:
        level = "MEDIUM RISK"
    else:
        level = "LOW RISK"

    return disease, level, round(probability * 100, 2)

# ================= ALERT BUILD =================
def build_alert(disease, level, probability):
    messages = {
        "LOW RISK": f"Low risk detected for {disease}. Maintain a healthy lifestyle.",
        "MEDIUM RISK": f"Moderate risk detected for {disease}. Regular monitoring is advised.",
        "HIGH RISK": f"High risk detected for {disease}. Please consult a healthcare professional."
    }
    return {
        "level": level,
        "probability": probability,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "message": messages[level]
    }

# ================= DISTANCE HELPER =================
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return round(6371 * c, 2)

# ================= HUGGINGFACE AI =================
HF_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {hf_token}"}

def get_precautions_from_ai(disease, risk_level):
    prompt = f"""
You are a medical assistant.
Disease: {disease}
Risk level: {risk_level}
Provide:
- Precautions
- Diet recommendations
- Exercise suggestions
- Lifestyle changes
Use bullet points. Keep it simple.
"""
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 250, "temperature": 0.4}}
    try:
        response = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=40)
        if response.status_code != 200:
            return "⚠ AI service temporarily unavailable. Please try again."
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        return "⚠ AI returned unexpected format."
    except Exception as e:
        print("HF ERROR:", e)
        return "⚠ AI service unavailable."

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")

# ---------- AUTH ----------
@app.route("/login", methods=["GET", "POST"])
def loginPage():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]
        user = users_collection.find_one({"email": email})
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["fullname"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", message="Invalid email or password")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signupPage():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"].lower()
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        if password != confirm:
            return render_template("signup.html", message="Passwords do not match")
        if users_collection.find_one({"email": email}):
            return render_template("signup.html", message="Email already registered")
        user = {
            "fullname": fullname,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(user)
        return redirect(url_for("loginPage"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("loginPage"))

# ---------- DASHBOARD ----------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ---------- MODULE PAGES ----------
@app.route("/diabetes")
@login_required
def diabetesPage(): return render_template("diabetes.html")
@app.route("/cancer")
@login_required
def cancerPage(): return render_template("breast_cancer.html")
@app.route("/heart")
@login_required
def heartPage(): return render_template("heart.html")
@app.route("/kidney")
@login_required
def kidneyPage(): return render_template("kidney.html")
@app.route("/liver")
@login_required
def liverPage(): return render_template("liver.html")

# ---------- PREDICTION HANDLER ----------
TEMPLATE_MAP = {
    "Diabetes": "diabetes.html",
    "Heart Disease": "heart.html",
    "Breast Cancer": "breast_cancer.html",
    "Kidney Disease": "kidney.html",
    "Liver Disease": "liver.html"
}

def handle_prediction(form):
    # ---------- VALIDATION ----------
    numeric_fields = [
        "age", "systolic", "diastolic", "cholesterol", "hdl",
        "ldl", "triglycerides", "blood_sugar", "bmi", "hr"
    ]
    radio_fields = ["sex", "family_history", "smoking", "diabetes", "exercise_cp"]

    for field in numeric_fields:
        val = form.get(field)
        if val is None or val.strip() == "":
            return render_template("heart.html", message=f"{field.replace('_',' ').title()} cannot be empty")
        if float(val) < 0:
            return render_template("heart.html", message=f"{field.replace('_',' ').title()} cannot be negative")

    for field in radio_fields:
        if field not in form:
            return render_template("heart.html", message=f"Please select {field.replace('_',' ').title()}")

    # ---------- PREDICTION ----------
    try:
        disease, level, probability = predict_risk(form)
        alert = build_alert(disease, level, probability)
        ai_precautions = get_precautions_from_ai(disease, level)
        template_name = TEMPLATE_MAP.get(disease, "dashboard.html")
        return render_template(
            template_name,
            disease=disease,
            alert=alert,
            result_text=f"{level} detected for {disease}",
            precautions=ai_precautions
        )
    except Exception as e:
        print("Prediction error:", e)
        disease = detect_disease(form) or "dashboard"
        return render_template(TEMPLATE_MAP.get(disease, "dashboard.html"),
                               message="⚠ Invalid input. Please check all fields.")

@app.route("/predict", methods=["POST"])
@login_required
def predictPage(): return handle_prediction(request.form)
@app.route("/heart/predict", methods=["POST"])
@login_required
def heart_predict(): return handle_prediction(request.form)
@app.route("/kidney/predict", methods=["POST"])
@login_required
def kidney_predict(): return handle_prediction(request.form)
@app.route("/liver/predict", methods=["POST"])
@login_required
def liver_predict(): return handle_prediction(request.form)
@app.route("/diabetes/predict", methods=["POST"])
@login_required
def diabetes_predict(): return handle_prediction(request.form)

# ---------- HOSPITAL RECOMMENDATION ----------
@app.route("/hospitals_by_place")
def hospitals_by_place():
    place = request.args.get("place")
    if not place: return jsonify([])
    headers = {"User-Agent": "MedAlertAI"}
    def get_coordinates(query_place):
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": query_place, "format": "json", "limit": 1}
        res = requests.get(geo_url, params=geo_params, headers=headers, timeout=5).json()
        if not res: return None
        return float(res[0]["lat"]), float(res[0]["lon"])
    coords = get_coordinates(place) or get_coordinates(place + ", Hyderabad")
    if not coords: return jsonify([])
    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:15000,{lat},{lon});
      way["amenity"="hospital"](around:15000,{lat},{lon});
      relation["amenity"="hospital"](around:15000,{lat},{lon});
    );
    out center tags;
    """
    hospital_res = requests.post(overpass_url, data=query, timeout=10).json()
    hospitals = []
    for h in hospital_res.get("elements", []):
        h_lat = h.get("lat") or h.get("center", {}).get("lat")
        h_lon = h.get("lon") or h.get("center", {}).get("lon")
        if not h_lat or not h_lon: continue
        distance = haversine(lat, lon, h_lat, h_lon)
        hospitals.append({
            "name": h.get("tags", {}).get("name", "Hospital"),
            "address": h.get("tags", {}).get("addr:full", ""),
            "distance": round(distance, 2)
        })
    hospitals.sort(key=lambda x: x["distance"])
    return jsonify(hospitals)

@app.route("/hospitals_by_coords")
def hospitals_by_coords():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon: return jsonify([])
    lat = float(lat)
    lon = float(lon)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:3000,{lat},{lon});
      way["amenity"="hospital"](around:3000,{lat},{lon});
      relation["amenity"="hospital"](around:3000,{lat},{lon});
    );
    out center tags;
    """
    hospital_res = requests.post(overpass_url, data=query, timeout=10).json()
    hospitals = []
    for h in hospital_res.get("elements", []):
        h_lat = h.get("lat") or h.get("center", {}).get("lat")
        h_lon = h.get("lon") or h.get("center", {}).get("lon")
        if not h_lat or not h_lon: continue
        distance = haversine(lat, lon, h_lat, h_lon)
        hospitals.append({
            "name": h.get("tags", {}).get("name", "Hospital"),
            "address": h.get("tags", {}).get("addr:full", ""),
            "distance": round(distance, 2)
        })
    hospitals.sort(key=lambda x: x["distance"])
    return jsonify(hospitals)

# ================= MAIN =================
if __name__ == "__main__":
    app.run(debug=True)
