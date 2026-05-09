import paho.mqtt.client as mqtt
import os

# Config matches your app's default
BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "sensor/data"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker. Clearing topic: {TOPIC}")
    # Publish an empty retained message to clear it
    client.publish(TOPIC, payload="", qos=1, retain=True)
    print("✅ Cleared retained message!")
    client.disconnect()

client = mqtt.Client()
client.on_connect = on_connect

try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
except Exception as e:
    print(f"Error: {e}")
