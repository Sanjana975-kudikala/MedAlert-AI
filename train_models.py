import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import os

# Create models folder if not exists
os.makedirs("models", exist_ok=True)

# ==========================
# 1. DIABETES MODEL
# ==========================
print("Training Diabetes Model...")

diabetes = pd.read_csv("datasets/diabetes.csv")
X = diabetes.drop("Outcome", axis=1)
y = diabetes["Outcome"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression(max_iter=1000)
model.fit(X_scaled, y)

with open("models/diabetes.pkl", "wb") as f:
    pickle.dump((model, scaler), f)

print("✅ Diabetes model saved")


# ==========================
# 2. HEART DISEASE MODEL
# ==========================
# ==========================
# 2. HEART DISEASE MODEL
# ==========================
# Example: retraining Heart Disease model
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import pickle
import pandas as pd

# Load your dataset
df = pd.read_csv("datasets/heart.csv")  # make sure it has all 15 columns
X = df[[
    "age", "systolic", "diastolic", "cholesterol", "hdl", "ldl",
    "triglycerides", "blood_sugar", "bmi", "hr",
    "sex", "family_history", "smoking", "diabetes", "exercise_cp"
]]
y = df["target"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression()
model.fit(X_scaled, y)

# Save model + scaler
with open("models/heart.pkl", "wb") as f:
    pickle.dump((model, scaler), f)
print("✅ heart model saved")

# ==========================
# 3. KIDNEY DISEASE MODEL
# ==========================
import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Load dataset
df = pd.read_csv("datasets/kidney.csv")

# Select ONLY fields used in your form
FEATURES = [
    "blood_urea",
    "serum_creatinine",
    "hemoglobin",
    "specific_gravity",
    "albumin",
    "age"
]

TARGET = "classification"

# Keep only needed columns
df = df[FEATURES + [TARGET]]

# Convert target to binary
df[TARGET] = df[TARGET].map({"ckd": 1, "notckd": 0})

# Split X / y
X = df[FEATURES]
y = df[TARGET]

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train model
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(max_iter=1000)
model.fit(X_scaled, y)

# Save model + scaler
with open("models/kidney.pkl", "wb") as f:
    pickle.dump((model, scaler), f)

print("✅ Kidney model trained successfully")


# ==========================
# 4. LIVER DISEASE MODEL
# ==========================
print("Training Liver Disease Model...")

liver = pd.read_csv("datasets/liver.csv")
liver = liver.dropna()

X = liver.drop("Dataset", axis=1)
y = liver["Dataset"] - 1  # convert 1/2 → 0/1

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression(max_iter=1000)
model.fit(X_scaled, y)

with open("models/liver.pkl", "wb") as f:
    pickle.dump((model, scaler), f)

print("✅ Liver disease model saved")


# ==========================
# 5. BREAST CANCER MODEL
# ==========================
print("Training Breast Cancer Model...")

from sklearn.datasets import load_breast_cancer

data = load_breast_cancer()
X = data.data
y = data.target

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression(max_iter=1000)
model.fit(X_scaled, y)

with open("models/breast_cancer.pkl", "wb") as f:
    pickle.dump((model, scaler), f)

print("✅ Breast cancer model saved")

print("\n🎉 ALL MODELS TRAINED & SAVED SUCCESSFULLY!")
