import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_for_dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER = os.environ.get('MQTT_BROKER') or "127.0.0.1"
    MQTT_PORT = int(os.environ.get('MQTT_PORT') or 1883)
    MQTT_USERNAME = os.environ.get('MQTT_USERNAME') or "wangtran"
    MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD') or "1006"
    MQTT_TOPIC_RESULT = "stroke/result"
    MQTT_TOPIC_SENSOR = "sensor/data"
    FRONTEND_API_URL = os.environ.get('FRONTEND_API_URL') or 'http://16.176.144.164:5000'
