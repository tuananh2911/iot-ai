import json
import pickle

import pandas as pd
import psycopg2
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
class AutoView():
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.user_data_set(self)
        self.load_model()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("topic/data")
    def on_message(self, client, userdata, msg):
        print(f"Message received: {msg.topic} {str(msg.payload)}")
        data = json.loads(msg.payload)
        required_fields = ['temperature', 'temperatureOut', 'humidity', 'lux', 'isLight', 'isRain', 'time']
        if all(field in data for field in required_fields):
            userdata.save_to_database(data)
            prediction_data = userdata.prepare_data_for_prediction(data)
            print(prediction_data)
            # Dự đoán thời tiết
            rain_prediction = userdata.predict_rain(prediction_data)

            if rain_prediction:
                emails = self.get_user_emails()
                for email in emails:
                    userdata.send_email(email,"Rain Alert", "Rain is predicted in the next hour.")
        else:
            print("Message does not contain all required data fields.")

    def send_email(self, to_email, subject, message):
        try:
            # Cấu hình thông tin email
            sender_email = "iotsystem2911@gmail.com"
            sender_password = "ebhpjrvduucbhkbf"
            smtp_server = "smtp.gmail.com"
            smtp_port = 587  # Sử dụng 465 cho kết nối SSL

            # Tạo nội dung email
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = to_email

            # Kết nối tới server và gửi email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Kích hoạt TLS
            server.login(sender_email, sender_password)
            server.send_message(msg)

            # Đóng kết nối server
            server.quit()
            print("Email sent successfully to", to_email)

        except Exception as e:
            print(f"Error sending email: {e}")
    def prepare_data_for_prediction(self, data):
        exog_data = pd.DataFrame({'temperature': data['temperatureOut'], 'humidity': data['humidity'], 'lux': data['lux']}, index=[0])
        return exog_data
    def get_user_emails(self):
        try:
            conn = psycopg2.connect(
                dbname="iot",
                user="postgres",
                password="29112002",
                host="103.77.246.226",
                port="5433"  # Cổng mặc định cho PostgreSQL
            )
            cursor = conn.cursor()

            # Truy vấn để lấy địa chỉ email của người dùng
            query = "SELECT email FROM public.user"  # Thay đổi câu lệnh SQL theo cơ sở dữ liệu của bạn
            cursor.execute(query)
            emails = cursor.fetchall()  # Lấy tất cả kết quả truy vấn

            cursor.close()
            conn.close()

            return [email[0] for email in emails]

        except Exception as e:
            print(f"Error fetching emails from database: {e}")
            return []

    def load_model(self):
        with open('sarimax_model.pkl', 'rb') as pkl:
            self.model = pickle.load(pkl)

    def predict_rain(self, data):
        prediction = self.model.forecast(steps=1,exog=data)
        print('prediction',prediction)
        if(prediction[0] > 0.5):
            return 1
        else:
            return 0
    def save_to_database(self, data):
        user_emails = self.get_user_emails()
        for to_email in user_emails:
            try:
                # Kết nối tới cơ sở dữ liệu
                conn = psycopg2.connect(
                    dbname="iot",
                    user="postgres",
                    password="29112002",
                    host="103.77.246.226",
                    port="5433"  # Cổng mặc định cho PostgreSQL
                )
                cursor = conn.cursor()

                # Chuẩn bị câu lệnh SQL
                insert_query = """
                    INSERT INTO sensor (temperature, temperature_out, humidity, lux, fan_speed, pump_speed, is_light, is_rain) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                data_to_insert = (
                    data['temperature'],
                    data['temperatureOut'],
                    data['humidity'],
                    data['lux'],
                    data.get('fanSpeed', None),  # Giả sử bạn có trường này trong dữ liệu của mình
                    data.get('pumpSpeed', None),  # Tương tự như trên
                    data['isLight'],
                    data['isRain']
                )

                # Thực hiện việc chèn dữ liệu
                cursor.execute(insert_query, data_to_insert)
                conn.commit()

                # Đóng kết nối
                cursor.close()
                conn.close()

            except Exception as e:
                print(f"Error saving data to database: {e}")
view = AutoView()
view.client.connect("103.77.246.226", 1883, 60)
view.client.loop_forever()