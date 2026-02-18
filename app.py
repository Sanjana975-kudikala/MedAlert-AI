from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import pickle
import numpy as np
import pandas as pd
import os
import requests
import time
from math import radians, cos, sin, asin, sqrt
from dotenv import load_dotenv
from groq import Groq  # Import Groq library

# Load environment variables
load_dotenv()

# ================= APP SETUP =================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ================= ENV VARIABLES =================
MONGO_URI = os.getenv("MONGO_URI")
# Add your GROQ_API_KEY to your .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in environment variables")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize Groq Client
groq_client = Groq(api_key=GROQ_API_KEY)

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
    if "pregnancies" in keys: return "Diabetes"
    if "radius_mean" in keys: return "Breast Cancer"
    if "systolic" in keys: return "Heart Disease"
    if "blood_urea" in keys: return "Kidney Disease"
    if "total_bilirubin" in keys: return "Liver Disease"
    return None

# ================= AI RECOMMENDATIONS (GROQ UPDATED) =================
def get_precautions_from_ai(disease, risk_level):
    try:
        # Professional medical prompt
        prompt = (
            f"You are a professional medical assistant. A patient has been screened for {disease} "
            f"and the result is {risk_level}. Provide 4 brief, actionable, and medically sound bullet points "
            f"covering precautions, diet, and lifestyle changes tailored specifically to this risk level. "
            f"Keep the response professional and concise."
        )

        # Updated model to llama-3.1-8b-instant to fix decommissioned error
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant providing evidence-based advice."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.5,
            max_tokens=300
        )
        
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq API Error: {e}")
        return "⚠️ AI health recommendations are temporarily unavailable. Please consult a doctor."
# ================= PREDICTION LOGIC =================
# ================= PREDICTION LOGIC (UPDATED) =================
def predict_risk(form):
    disease = detect_disease(form)
    bundle = MODELS.get(disease)
    if not bundle: raise ValueError("Model not loaded")

    model = bundle["model"]
    scaler = bundle["scaler"]

    feature_map = {
        "Diabetes": ["fbg", "hba1c", "rbs", "systolic", "bmi", "age", "family_history", "pregnancies"],
        "Heart Disease": ["age", "systolic", "diastolic", "cholesterol", "hdl", "ldl", 
                          "triglycerides", "blood_sugar", "bmi", "hr", "sex", 
                          "family_history", "smoking", "diabetes", "exercise_cp"],
        "Liver Disease": ["Age", "Total_Bilirubin", "Direct_Bilirubin", "Alkaline_Phosphotase", 
                          "Alamine_Aminotransferase", "Aspartate_Aminotransferase", 
                          "Total_Proteins", "Albumin", "Albumin_and_Globulin_Ratio"],
        "Breast Cancer": ["mean radius", "mean texture", "mean perimeter", "mean area"],
        "Kidney Disease": ["blood_urea", "serum_creatinine", "hemoglobin", "specific_gravity", "albumin", "age"]
    }

    # ===== VALUE EXTRACTION (Fixed for 400 Errors) =====
    if disease == "Diabetes":
        bp = form["blood_pressure"]
        systolic = float(bp.split("/")[0])
        values = np.array([[float(form["fbg"]), float(form["hba1c"]), float(form["rbs"]), 
                           systolic, float(form["bmi"]), float(form["age"]), 
                           float(form["family_history"]), float(form["pregnancies"])]])
                           
    elif disease == "Heart Disease":
        values = np.array([[float(form[f]) for f in feature_map["Heart Disease"]]])
        
    elif disease == "Liver Disease":
        # Using exact name attributes from liver.html
        values = np.array([[
            float(form["age"]),
            float(form["total_bilirubin"]),
            float(form["direct_bilirubin"]),
            float(form["alkphos"]),
            float(form["sgpt"]),
            float(form["sgot"]),
            float(form["total_proteins"]),
            float(form["albumin"]),
            float(form["ag_ratio"])
        ]])
        
    elif disease == "Kidney Disease":
        values = np.array([[float(form[f]) for f in feature_map["Kidney Disease"]]])
        
    elif disease == "Breast Cancer":
        # Using exact name attributes from breast_cancer.html
        values = np.array([[
            float(form["radius_mean"]),
            float(form["texture_mean"]),
            float(form["perimeter_mean"]),
            float(form["area_mean"])
        ]])
    else:
        values = np.array([float(v) for v in form.values()]).reshape(1, -1)

    # Convert to DataFrame with feature_map names to satisfy scaler requirements
    values_df = pd.DataFrame(values, columns=feature_map[disease])
    values_scaled = scaler.transform(values_df)
    
    probability = model.predict_proba(values_scaled)[0][1]
    level = "HIGH RISK" if probability >= 0.7 else "MEDIUM RISK" if probability >= 0.5 else "LOW RISK"

    return disease, level, round(probability * 100, 2)
# ================= ALERT BUILD =================
def build_alert(disease, level, probability):
    messages = {
        "LOW RISK": f"Low risk detected for {disease}. Maintain a healthy lifestyle.",
        "MEDIUM RISK": f"Moderate risk detected for {disease}. Regular monitoring is advised.",
        "HIGH RISK": f"High risk detected for {disease}. Please consult a healthcare professional."
    }
    return {
        "level": level, "probability": probability,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "message": messages[level]
    }

# ================= DISTANCE HELPER =================
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return round(6371 * 2 * asin(sqrt(a)), 2)

# ================= ROUTES =================
@app.route("/")
def home(): return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def loginPage():
    if request.method == "POST":
        user = users_collection.find_one({"email": request.form["email"].lower()})
        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session["user_id"], session["user_name"] = str(user["_id"]), user["fullname"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", message="Invalid email or password")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signupPage():
    if request.method == "POST":
        if users_collection.find_one({"email": request.form["email"].lower()}):
            return render_template("signup.html", message="Email already registered")
        users_collection.insert_one({
            "fullname": request.form["fullname"],
            "email": request.form["email"].lower(),
            "password_hash": generate_password_hash(request.form["password"]),
            "created_at": datetime.utcnow()
        })
        return redirect(url_for("loginPage"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("loginPage"))

@app.route("/dashboard")
@login_required
def dashboard(): return render_template("dashboard.html")

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

def handle_prediction(form):
    try:
        disease, level, probability = predict_risk(form)
        return render_template(
            "predict.html",
            disease=disease,
            alert=build_alert(disease, level, probability),
            result_text=f"{level} detected for {disease}",
            precautions=get_precautions_from_ai(disease, level)
        )
    except Exception as e:
        return f"Error occurred: {str(e)}"

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

@app.route("/hospitals_by_place")
def hospitals_by_place():
    place = request.args.get("place")
    if not place: return jsonify([])
    res = requests.get("https://nominatim.openstreetmap.org/search", params={"q": place, "format": "json", "limit": 1}, headers={"User-Agent": "MedAlertAI"}).json()
    if not res: return jsonify([])
    lat, lon = float(res[0]["lat"]), float(res[0]["lon"])
    query = f'[out:json];(node["amenity"="hospital"](around:15000,{lat},{lon}););out center tags;'
    hospital_res = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=10).json()
    hospitals = [{"name": h.get("tags", {}).get("name", "Hospital"), "address": h.get("tags", {}).get("addr:full", ""), "distance": haversine(lat, lon, h.get("lat") or h.get("center", {}).get("lat"), h.get("lon") or h.get("center", {}).get("lon"))} for h in hospital_res.get("elements", [])]
    return jsonify(sorted(hospitals, key=lambda x: x["distance"]))

if __name__ == "__main__": 
    app.run(debug=True)