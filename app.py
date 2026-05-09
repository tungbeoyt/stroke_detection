import json
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from types import SimpleNamespace

import pandas as pd
import warnings
import paho.mqtt.client as mqtt
import joblib
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier

import threading
import os
import time
import requests
from config import Config
from dotenv import load_dotenv

warnings.filterwarnings('ignore')
load_dotenv()

app = Flask(__name__, template_folder='templates')
CORS(app)
app.config.from_object(Config)

db = SQLAlchemy(app)

# --- ZALO BOT SETUP ---
from zalo_module import start_zalo_bot, zalo_send_message

# Start Zalo Bot Thread
# Thread is started in main block after DB creation to avoid circular issues or early access


# --- MQTT SETUP ---
broker = app.config['MQTT_BROKER']
port = app.config['MQTT_PORT']
topic_result = app.config['MQTT_TOPIC_RESULT']
topic_sensor = app.config['MQTT_TOPIC_SENSOR']
mqtt_username = app.config['MQTT_USERNAME']
mqtt_password = app.config['MQTT_PASSWORD']

latest_data_from_mqtt = {
    'heart_rate': None,
    'spo2': None,
    'timestamp': 0
}

# --- HELPER: PERFORM PREDICTION ---
def perform_prediction_and_alert(user_profile, heart_rate, spo2):
    """
    Common function to predict stroke risk and send alerts.
    Used by both /predict API (Web) and MQTT Callback (Headless).
    """
    if model is None or preprocessor is None:
        print("❌ Model not ready")
        return None, 0

    input_data = {
        'gender': user_profile.gender,
        'age': user_profile.age,
        'hypertension': user_profile.hypertension,
        'heart_disease': user_profile.heart_disease,
        'ever_married': user_profile.ever_married,
        'work_type': user_profile.work_type,
        'Residence_type': user_profile.residence_type,
        'avg_glucose_level': user_profile.avg_glucose_level,
        'bmi': user_profile.bmi,
        'smoking_status': user_profile.smoking_status,
        'Heart Rate': float(heart_rate),
        'SpO2': float(spo2)
    }

    try:
        input_df = pd.DataFrame([{
            'gender': input_data['gender'],
            'age': float(input_data['age']),
            'hypertension': int(input_data['hypertension']),
            'heart_disease': int(input_data['heart_disease']),
            'ever_married': input_data['ever_married'],
            'work_type': input_data['work_type'],
            'Residence_type': input_data['Residence_type'],
            'avg_glucose_level': float(input_data['avg_glucose_level']),
            'bmi': float(input_data['bmi']),
            'smoking_status': input_data['smoking_status'],
            'Heart Rate': heart_rate,
            'SpO2': spo2
        }])
        
        # 3. Preprocess
        input_encoded = preprocessor.transform(input_df)
        prediction = model.predict(input_encoded)[0]
        probability = 0
        if hasattr(model, "predict_proba"):
             probability = model.predict_proba(input_encoded)[0][1]
        
        # --- Notifications ---
        # 1. MQTT Feedback
        if mqtt_client:
             mqtt_topic_msg = "STROKE" if prediction == 1 else "NORMAL"
             mqtt_client.publish(topic_result, mqtt_topic_msg)

        # 2. Alerts (Only if High Risk)
        if prediction == 1:
             print(f"⚠️ HIGH RISK DETECTED for {user_profile.username}! Prob: {probability:.2f}")
             
             # ZALO ALERT
             if user_profile.zalo_id:
                 warning_msg = f"⚠️ CẢNH BÁO ĐỘT QUỴ TỰ ĐỘNG!\nBệnh nhân: {user_profile.fullname}\nNguy cơ: CAO ({probability:.2%})\nHãy kiểm tra ngay lập tức!"
                 zalo_send_message(user_profile.zalo_id, warning_msg)

        return prediction, probability

    except Exception as e:
        print(f"Prediction Error: {e}")
        return None, 0

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(topic_sensor)

def on_message(client, userdata, msg):
    global latest_data_from_mqtt
    payload = msg.payload.decode()
    print("Received:", payload)
    try:
        data = json.loads(payload)
        hr = float(data.get("bpm", 0))
        spo2 = float(data.get("spo2", 0))
        
        latest_data_from_mqtt["heart_rate"] = hr
        latest_data_from_mqtt["spo2"] = spo2
        latest_data_from_mqtt["timestamp"] = int(round(time.time() * 1000))
        print("✅ Updated:", latest_data_from_mqtt)
        
        # --- HEADLESS PREDICTION ---
        # Auto-predict for users who have Zalo linked (active monitoring)
        with app.app_context():
            # Find users to monitor. For now, pick the first user with zalo_id linked.
            # In a real app, you might map Device ID -> User.
            monitored_user = User.query.filter(User.zalo_id != None).first()
            
            if monitored_user and hr > 0:
                print(f"🔄 Auto-Analyzing for user: {monitored_user.username}")
                perform_prediction_and_alert(monitored_user, hr, spo2)
                
    except Exception as e:
        print("❌ MQTT/Auto-Predict Error:", e)

try:
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(mqtt_username, mqtt_password)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(broker, port)

    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
    mqtt_thread.daemon = True
    mqtt_thread.start()
except Exception as e:
    print(f"Could not connect to MQTT broker: {e}")
    mqtt_client = None

# --- AI MODEL LOAD ---
model = None
preprocessor = None
feature_names = None

def load_trained_assets():
    global model, preprocessor, feature_names
    try:
        model = joblib.load('stroke_xgb_model.pkl')
        preprocessor = joblib.load('preprocessor.pkl')
        print("Trained model and preprocessor loaded successfully.")

        global categorical_features_for_app, numerical_features_for_app
        categorical_features_for_app = ['gender', 'ever_married', 'work_type', 'Residence_type', 'smoking_status']
        numerical_features_for_app = ['age', 'avg_glucose_level', 'bmi', 'hypertension', 'heart_disease', 'Heart Rate', 'SpO2']

        all_features_after_preprocessing = preprocessor.get_feature_names_out()
        feature_names = list(all_features_after_preprocessing)
        print("Feature names after preprocessing:", feature_names)

    except FileNotFoundError:
        print("Error: Trained model or preprocessor not found. Please run 'train_model.py' first.")
        return
    except Exception as e:
        print(f"Error loading trained assets: {e}")
        return

with app.app_context():
    db.create_all()
    load_trained_assets()

# --- DB MODEL ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    hypertension = db.Column(db.Integer, nullable=False)
    heart_disease = db.Column(db.Integer, nullable=False)
    ever_married = db.Column(db.String(10), nullable=False)
    work_type = db.Column(db.String(50), nullable=False)
    residence_type = db.Column(db.String(10), nullable=False)
    avg_glucose_level = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    smoking_status = db.Column(db.String(50), nullable=False)
    zalo_id = db.Column(db.String(50), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# --- ROUTES ---
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/config')
def get_config():
    return jsonify({'FRONTEND_API_URL': app.config['FRONTEND_API_URL']})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Username or email already exists'}), 409

    new_user = User(
        fullname=data['fullname'],
        username=data['username'],
        email=data['email'],
        gender=data['gender'],
        age=data['age'],
        hypertension=data['hypertension'],
        heart_disease=data['heart_disease'],
        ever_married=data['ever_married'],
        work_type=data['work_type'],
        residence_type=data['residence_type'],
        avg_glucose_level=data['avg_glucose_level'],
        bmi=data['bmi'],
        smoking_status=data['smoking_status']
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        return jsonify({'message': 'Login successful', 'user': {'username': user.username}}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    user_profile = User.query.filter_by(username=data.get('username')).first()

    if not user_profile:
        return jsonify({'message': 'User not found'}), 404

    if model is None or preprocessor is None:
        return jsonify({'message': 'AI model not ready. Please run train_model.py first.'}), 503

    # --- PRIORITY: Use Manual Input Data if available, fallback to DB ---
    # We create a placeholder object that mimics the User model
    manual_profile = SimpleNamespace()
    manual_profile.username = user_profile.username
    manual_profile.fullname = user_profile.fullname
    manual_profile.zalo_id = user_profile.zalo_id # Keep sending alerts if configured
    
    # Map fields (Input from Request > DB Value)
    manual_profile.age = int(data.get('age', user_profile.age))
    manual_profile.gender = data.get('gender', user_profile.gender)
    manual_profile.hypertension = int(data.get('hypertension', user_profile.hypertension))
    manual_profile.heart_disease = int(data.get('heart_disease', user_profile.heart_disease))
    manual_profile.ever_married = data.get('ever_married', user_profile.ever_married)
    manual_profile.work_type = data.get('work_type', user_profile.work_type)
    manual_profile.residence_type = data.get('residence_type', user_profile.residence_type)
    manual_profile.avg_glucose_level = float(data.get('avg_glucose_level', user_profile.avg_glucose_level))
    manual_profile.bmi = float(data.get('bmi', user_profile.bmi))
    manual_profile.smoking_status = data.get('smoking_status', user_profile.smoking_status)

    # Prepare input data for prediction
    heart_rate = float(data.get('heart_rate', latest_data_from_mqtt['heart_rate'] or 0))
    spo2 = float(data.get('spo2', latest_data_from_mqtt['spo2'] or 0))

    prediction, probability = perform_prediction_and_alert(manual_profile, heart_rate, spo2)
    
    if prediction is None:
         return jsonify({'message': 'Prediction failed internally'}), 500

    result_text = "Nguy cơ đột quỵ" if prediction == 1 else "Bình thường"
    
    return jsonify({
        'result': result_text,
        'probability': f"{probability:.4f}",
        'heart_rate': heart_rate,
        'spo2': spo2
    }), 200

@app.route('/sensor-data')
def sensor_data():
    data = latest_data_from_mqtt.copy()
    if data['timestamp'] == 0:
        data['seconds_ago'] = None
    else:
        current_time = int(round(time.time() * 1000))
        data['seconds_ago'] = (current_time - data['timestamp']) / 1000.0
    return jsonify(data)

@app.route('/api/profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')
    if not username: return jsonify({'message': 'Username is required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user: return jsonify({'message': 'User not found'}), 404
    return jsonify({
        'fullname': user.fullname,
        'username': user.username,
        'email': user.email,
        'gender': user.gender,
        'age': user.age,
        'work_type': user.work_type,
        'residence_type': user.residence_type,
        'ever_married': user.ever_married,
        'smoking_status': user.smoking_status,
        'bmi': user.bmi,
        'avg_glucose_level': user.avg_glucose_level,
        'hypertension': user.hypertension,
        'heart_disease': user.heart_disease
    }), 200

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    data = request.get_json()
    username = data.get('username')
    if not username: return jsonify({'message': 'Username is required'}), 400 
    user = User.query.filter_by(username=username).first()
    if not user: return jsonify({'message': 'User not found'}), 404
    try:
        if 'age' in data: user.age = int(data['age'])
        if 'gender' in data: user.gender = data['gender']
        if 'bmi' in data: user.bmi = float(data['bmi'])
        if 'avg_glucose_level' in data: user.avg_glucose_level = float(data['avg_glucose_level'])
        if 'hypertension' in data: user.hypertension = int(data['hypertension'])
        if 'heart_disease' in data: user.heart_disease = int(data['heart_disease'])
        if 'work_type' in data: user.work_type = data['work_type']
        if 'residence_type' in data: user.residence_type = data['residence_type']
        if 'smoking_status' in data: user.smoking_status = data['smoking_status']
        if 'ever_married' in data: user.ever_married = data['ever_married']
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating profile: {e}")
        return jsonify({'message': 'Failed to update profile'}), 500

# Helper to access sensor data from another thread
def get_current_sensor_data():
    data = latest_data_from_mqtt.copy()
    if data['timestamp'] != 0:
        current_time = int(round(time.time() * 1000))
        data['seconds_ago'] = (current_time - data['timestamp']) / 1000.0
    else:
        data['seconds_ago'] = None
    return data

# Start Zalo Bot (POLLING MODE)
# WARNING: With multiple gunicorn workers, this will start multiple bot threads.
# For production, utilize a separate worker process or single gunicorn worker.
start_zalo_bot(app, db, User, get_current_sensor_data)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=5000, host='0.0.0.0')
