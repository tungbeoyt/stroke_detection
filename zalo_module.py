import requests
import time
import threading
import os

ZALO_BOT_TOKEN = os.getenv("ZALO_BOT_TOKEN")
ZALO_BASE_URL = f"https://bot-api.zaloplatforms.com/bot{ZALO_BOT_TOKEN}"

def zalo_get_updates(offset=None):
    url = f"{ZALO_BASE_URL}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Zalo Bot Error (getUpdates): {e}")
        return None

def zalo_send_message(chat_id, text):
    url = f"{ZALO_BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"✅ Zalo Sent: {text}")
    except Exception as e:
        print(f"❌ Zalo Send Error: {e}")

def zalo_process_update(update, app_context, db, User_model, get_sensor_data_callback=None):
    try:
        if "result" not in update: return
        result = update["result"]
        event_name = result.get("event_name")
        
        if event_name == "message.text.received":
            message = result.get("message")
            if not message: return
            text = message.get("text")
            chat_id = message.get("chat", {}).get("id") or message.get("from", {}).get("id")
            
            if chat_id and text:
                print(f"📩 Zalo Msg from {chat_id}: {text}")
                msg_lower = text.lower().strip()
                
                # --- COMMANDS ---

                # 1. LOGIN
                if msg_lower.startswith("login"):
                    parts = text.split()
                    if len(parts) == 3:
                        username, password = parts[1], parts[2]
                        with app_context:
                            user = User_model.query.filter_by(username=username).first()
                            if user and user.check_password(password):
                                user.zalo_id = chat_id
                                db.session.commit()
                                zalo_send_message(chat_id, f"✅ Liên kết thành công!\nChào {user.fullname}, tôi sẽ gửi cảnh báo cho bạn tại đây.")
                            else:
                                zalo_send_message(chat_id, "❌ Sai tên đăng nhập hoặc mật khẩu.")
                    else:
                        zalo_send_message(chat_id, "⚠️ Cú pháp sai. Hãy gõ: login <tên_đăng_nhập> <mật_khẩu>")
                    return

                # Check if user is linked for other commands
                current_user = None
                with app_context:
                    current_user = User_model.query.filter_by(zalo_id=chat_id).first()

                # 2. PROFILE (SHOW ALL LINKED PROFILES)
                if msg_lower == "profile":
                    linked_users = []
                    with app_context:
                        linked_users = User_model.query.filter_by(zalo_id=chat_id).all()

                    if not linked_users:
                        zalo_send_message(chat_id, "❌ Bạn chưa đăng nhập.\n👉 Hãy gõ: login <tên_đăng_nhập> <mật_khẩu>")
                        return

                    msg = f"📋 DANH SÁCH HỒ SƠ ({len(linked_users)} người)\n━━━━━━━━━━━━━━━━\n"
                    
                    # Translation Dictionaries
                    trans_gender = {"Male": "Nam", "Female": "Nữ", "Other": "Khác"}
                    trans_married = {"Yes": "Đã kết hôn", "No": "Độc thân"}
                    trans_work = {
                        "Private": "Tư nhân", "Self-employed": "Tự kinh doanh",
                        "Govt_job": "Nhà nước", "children": "Trẻ em", "Never_worked": "Chưa đi làm"
                    }
                    trans_residence = {"Urban": "Thành thị", "Rural": "Nông thôn"}
                    trans_smoking = {
                        "formerly smoked": "Đã từng hút", "never smoked": "Không hút",
                        "smokes": "Đang hút", "Unknown": "Không rõ"
                    }

                    for i, u in enumerate(linked_users, 1):
                        gender_vi = trans_gender.get(u.gender, u.gender)
                        married_vi = trans_married.get(u.ever_married, u.ever_married)
                        work_vi = trans_work.get(u.work_type, u.work_type)
                        residence_vi = trans_residence.get(u.residence_type, u.residence_type)
                        smoking_vi = trans_smoking.get(u.smoking_status, u.smoking_status)

                        msg += (
                            f"{i}. {u.fullname} (@{u.username})\n"
                            f"   🎂 Tuổi: {u.age} | 🚻 {gender_vi}\n"
                            f"   ⚖️ BMI: {u.bmi} | 🩸 ĐH: {u.avg_glucose_level}\n"
                            f"   ⚠️ Huyết áp: {'Có' if u.hypertension else 'Không'}\n"
                            f"   💔 Bệnh tim: {'Có' if u.heart_disease else 'Không'}\n"
                            f"   💍 Kết hôn: {married_vi}\n"
                            f"   💼 Công việc: {work_vi}\n"
                            f"   🏠 Nơi ở: {residence_vi}\n"
                            f"   🚬 Hút thuốc: {smoking_vi}\n"
                            f"----------------\n"
                        )
                    
                    msg += "━━━━━━━━━━━━━━━━"
                    zalo_send_message(chat_id, msg)
                    return

                # 3. HEALTH (LIVE SENSOR DATA)
                if msg_lower.startswith("health"):
                    # NOTE: Currently sensor data is global (latest from MQTT).
                    # In a real multi-device setup, we'd need DeviceID mapped to User.
                    # For now, we just check if the user is linked.
                    
                    linked_users = []
                    with app_context:
                        linked_users = User_model.query.filter_by(zalo_id=chat_id).all()
                    
                    if not linked_users:
                        zalo_send_message(chat_id, "❌ Bạn chưa đăng nhập.\n👉 Hãy gõ: login <tên_đăng_nhập> <mật_khẩu>")
                        return

                    # Just show data, but warn if multiple users exist and we can't distinguish devices yet
                    warning_note = ""
                    if len(linked_users) > 1:
                         warning_note = "\n(Lưu ý: Dữ liệu này là từ thiết bị đang kết nối gần nhất)"

                    if get_sensor_data_callback:
                        data = get_sensor_data_callback()
                        hr = data.get('heart_rate')
                        spo2 = data.get('spo2')
                        last_update = data.get('seconds_ago')
                        
                        if hr and spo2 and last_update is not None and last_update < 60:
                            status = "🟢 Ổn định" if (60 <= hr <= 100 and spo2 >= 95) else "🔴 Cần chú ý"
                            health_msg = (
                                f"💓 SỨC KHỎE HIỆN TẠI{warning_note}\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"❤️ Nhịp tim: {hr} bpm\n"
                                f"💨 SpO2: {spo2}%\n"
                                f"🕒 Cập nhật: {int(last_update)}s trước\n"
                                f"----------------\n"
                                f"Đánh giá: {status}"
                            )
                            zalo_send_message(chat_id, health_msg)
                        else:
                            zalo_send_message(chat_id, "⚠️ Không có dữ liệu cảm biến (hoặc thiết bị tắt).")
                    else:
                        zalo_send_message(chat_id, "⚠️ Lỗi kết nối dữ liệu.")
                    return

                # 4. DEFAULT / HELP MENU
                menu_msg = (
                    f"🤖 TRỢ LÝ SỨC KHỎE\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Gõ các lệnh sau để nhận hỗ trợ:\n\n"
                    f"1️⃣  [ profile ]\n"
                    f"      ➤ Xem tất cả hồ sơ\n\n"
                    f"2️⃣  [ health ]\n"
                    f"      ➤ Xem nhịp tim & SpO2\n\n"
                    f"3️⃣  [ login <user> <pass> ]\n"
                    f"      ➤ Liên kết tài khoản\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"💡 Ví dụ: gõ 'health' để kiểm tra."
                )
                zalo_send_message(chat_id, menu_msg)

    except Exception as e:
        print(f"❌ Zalo Process Error: {e}")

def zalo_bot_loop(app, db, User_model, get_sensor_data_callback=None):
    print("🚀 Zalo Bot Thread Started")
    if not ZALO_BOT_TOKEN:
        print("❌ Missing ZALO_BOT_TOKEN")
        return

    while True:
        try:
            updates = zalo_get_updates()
            if updates and updates.get("ok"):
                res = updates.get("result")
                if isinstance(res, list):
                    for item in res:
                        zalo_process_update({"result": item}, app.app_context(), db, User_model, get_sensor_data_callback)
                elif isinstance(res, dict):
                        zalo_process_update(updates, app.app_context(), db, User_model, get_sensor_data_callback)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Zalo Loop Error: {e}")
            time.sleep(5)

def start_zalo_bot(app, db, User_model, get_sensor_data_callback=None):
    """Starts the Zalo Bot in a background thread."""
    thread = threading.Thread(target=zalo_bot_loop, args=(app, db, User_model, get_sensor_data_callback), daemon=True)
    thread.start()
