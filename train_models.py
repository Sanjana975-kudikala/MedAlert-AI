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
print("Training Heart Disease Model...")

# Load your dataset
df_heart = pd.read_csv("datasets/heart.csv") 
X_heart = df_heart[[
    "age", "systolic", "diastolic", "cholesterol", "hdl", "ldl",
    "triglycerides", "blood_sugar", "bmi", "hr",
    "sex", "family_history", "smoking", "diabetes", "exercise_cp"
]]
y_heart = df_heart["target"]

scaler_heart = StandardScaler()
X_scaled_heart = scaler_heart.fit_transform(X_heart)

model_heart = LogisticRegression(max_iter=1000)
model_heart.fit(X_scaled_heart, y_heart)

# Save model + scaler
with open("models/heart.pkl", "wb") as f:
    pickle.dump((model_heart, scaler_heart), f)
print("✅ heart model saved")


# ==========================
# 3. KIDNEY DISEASE MODEL
# ==========================
# ==========================
# 3. KIDNEY DISEASE MODEL (Updated)
# ==========================
print("Training Kidney Disease Model...")

df_kidney = pd.read_csv("datasets/kidney.csv")

# Select ONLY fields used in your kidney.html form
KIDNEY_FEATURES = [
    "blood_urea",
    "serum_creatinine",
    "hemoglobin",
    "specific_gravity",
    "albumin",
    "age"
]

# Ensure the CSV has a target column. 
# If your CSV uses a different name for the result, change 'classification' below.
TARGET_KIDNEY = "classification" 

if TARGET_KIDNEY in df_kidney.columns:
    df_kidney = df_kidney[KIDNEY_FEATURES + [TARGET_KIDNEY]]
    df_kidney[TARGET_KIDNEY] = df_kidney[TARGET_KIDNEY].map({"ckd": 1, "notckd": 0})
    
    X_kidney = df_kidney[KIDNEY_FEATURES]
    y_kidney = df_kidney[TARGET_KIDNEY]

    scaler_kidney = StandardScaler()
    X_scaled_kidney = scaler_kidney.fit_transform(X_kidney)

    model_kidney = LogisticRegression(max_iter=1000)
    model_kidney.fit(X_scaled_kidney, y_kidney)

    with open("models/kidney.pkl", "wb") as f:
        pickle.dump((model_kidney, scaler_kidney), f)
    print("✅ Kidney model trained successfully")
else:
    print(f"❌ Error: {TARGET_KIDNEY} column missing in kidney.csv. Skipping...")

# ==========================
# 4. LIVER DISEASE MODEL
# ==========================
print("Training Liver Disease Model...")

liver = pd.read_csv("datasets/liver.csv")
liver = liver.dropna()

X_liver = liver.drop("Dataset", axis=1)
y_liver = liver["Dataset"] - 1  # convert 1/2 → 0/1

scaler_liver = StandardScaler()
X_scaled_liver = scaler_liver.fit_transform(X_liver)

model_liver = LogisticRegression(max_iter=1000)
model_liver.fit(X_scaled_liver, y_liver)

with open("models/liver.pkl", "wb") as f:
    pickle.dump((model_liver, scaler_liver), f)

print("✅ Liver disease model saved")


# ==========================
# 5. BREAST CANCER MODEL (Updated)
# ==========================
print("Training Breast Cancer Model...")

from sklearn.datasets import load_breast_cancer

data = load_breast_cancer()
# Create a DataFrame to easily select specific features
df_cancer = pd.DataFrame(data.data, columns=data.feature_names)

# Select ONLY the 4 features that match your breast_cancer.html inputs
CANCER_FEATURES = ['mean radius', 'mean texture', 'mean perimeter', 'mean area']
X_cancer = df_cancer[CANCER_FEATURES]
y_cancer = data.target

scaler_cancer = StandardScaler()
X_scaled_cancer = scaler_cancer.fit_transform(X_cancer)

model_cancer = LogisticRegression(max_iter=1000)
model_cancer.fit(X_scaled_cancer, y_cancer)

with open("models/breast_cancer.pkl", "wb") as f:
    pickle.dump((model_cancer, scaler_cancer), f)

print("✅ Breast cancer model saved with 4 features")

print("\n🎉 ALL MODELS TRAINED & SAVED SUCCESSFULLY!")