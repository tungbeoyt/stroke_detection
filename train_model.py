import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
import joblib

# Load the dataset
try:
    df = pd.read_csv('healthcare-dataset-stroke-data(3).csv')
except FileNotFoundError:
    print("Error: healthcare-dataset-stroke-data(3).csv not found. Please ensure the file is in the correct directory.")
    exit()

# Preprocessing
# Drop 'id' column as it's not relevant for training
df = df.drop('id', axis=1)

# Handle missing values for 'bmi' with the mean
df['bmi'].fillna(df['bmi'].mean(), inplace=True)

# Convert 'gender' to numerical, handling 'Other' if present
df['gender'] = df['gender'].replace('Other', df['gender'].mode()[0])

# Add 'Heart Rate' and 'SpO2' columns, initializing with 0 for training
# These will be updated with live MQTT data during prediction
# Using real Heart Rate and SpO2 data from the CSV file
# No synthetic data generation


# Define categorical and numerical features
categorical_features = ['gender', 'ever_married', 'work_type', 'Residence_type', 'smoking_status']
# Include 'hypertension', 'heart_disease', 'Heart Rate', 'SpO2' in numerical features
numerical_features = ['age', 'avg_glucose_level', 'bmi', 'hypertension', 'heart_disease', 'Heart Rate', 'SpO2']

# Create a column transformer for preprocessing
# Note: 'hypertension' and 'heart_disease' are already numerical and will be scaled by StandardScaler.
# 'Heart Rate' and 'SpO2' are also numerical and will be scaled.
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ],
    remainder='drop' # Drop any remaining columns not explicitly handled
)

# Separate features (X) and target (y)
X = df.drop('stroke', axis=1)
y = df['stroke']

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Preprocess the training data
X_train_preprocessed = preprocessor.fit_transform(X_train)
X_test_preprocessed = preprocessor.transform(X_test)

# Apply SMOTE to the preprocessed training data
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train_preprocessed, y_train)

# Initialize and train the XGBoost model
model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, random_state=42)
print("Training the model...")
model.fit(X_train_resampled, y_train_resampled)
print("Model training complete.")

# Save the trained model and preprocessor
joblib.dump(model, 'stroke_xgb_model.pkl')
joblib.dump(preprocessor, 'preprocessor.pkl')

print("Model and preprocessor saved successfully.")
