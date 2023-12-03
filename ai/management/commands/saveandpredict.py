import json
import pickle
from datetime import datetime
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pandas as pd
import psycopg2
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
class AutoView():
    def __init__(self):
        self.model_fit = None
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.user_data_set(self)
        self.load_model()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("topic/data")

    def query(self, conn):
        cursor = conn.cursor()
        query = """
            SET TIME ZONE 'Asia/Ho_Chi_Minh';
            WITH daylight_times AS (
                SELECT 
                    MIN(CASE WHEN lux > 100 AND EXTRACT(HOUR FROM time) >= 5 THEN time END) AS sunrise_time,
                    MAX(CASE WHEN lux <= 100 AND EXTRACT(HOUR FROM time) >= 17 THEN time END) AS sunset_time,
                    CURRENT_DATE
                FROM sensor
                WHERE DATE(time) = CURRENT_DATE
            ),
            sunny_moments AS (
                SELECT 
                    COUNT(*) AS sunny_moments_count
                FROM sensor
                WHERE DATE(time) = CURRENT_DATE
                AND time >= (SELECT sunrise_time FROM daylight_times)
                AND time <= (SELECT sunset_time FROM daylight_times)
                AND lux > 100
            )
            SELECT 
                MAX(temperature) AS max_temperature,
                MIN(humidity) AS min_humidity,
                ((SELECT sunny_moments_count FROM sunny_moments) * 20)::FLOAT / EXTRACT(EPOCH FROM ((SELECT sunset_time FROM daylight_times) - (SELECT sunrise_time FROM daylight_times))) AS percentage_of_sunshine
            FROM sensor
            WHERE DATE(time) = CURRENT_DATE;
            """
        cursor.execute(query)
        result = cursor.fetchone()
        conn.commit()

        # Đóng kết nối
        cursor.close()
        conn.close()
        return result
    def on_message(self, client, userdata, msg):
        try:
            print(f"Message received: {msg.topic} {str(msg.payload)}")
            data = json.loads(msg.payload)
            required_fields = ['temperature', 'temperatureOut', 'humidity', 'lux', 'isLight', 'isRain', 'time']
            if all(field in data for field in required_fields):
                conn = psycopg2.connect(
                    dbname="iot",
                    user="postgres",
                    password="29112002",
                    host="103.77.246.226",
                    port="5433"  # Cổng mặc định cho PostgreSQL
                )
                cursor = conn.cursor()
                userdata.save_to_database(data, conn)
                time_str = data['time']
                time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                print('time',time_obj.hour)

                # Kiểm tra xem có phải là 23 giờ không
                if time_obj.hour == 23:
                    print("Thời gian là 23 giờ.")
                    data_process = self.query(conn)
                    prediction_data = userdata.prepare_data_for_prediction(data_process)
                    rain_prediction = userdata.predict_rain(prediction_data)
                    if rain_prediction:
                        emails = self.get_user_emails()
                        for email in emails:
                            userdata.send_email(email,"Rain Alert", "Rain is predicted in the next day.")
                conn.commit()

                # Đóng kết nối
                cursor.close()
                conn.close()
            else:
                print("Message does not contain all required data fields.")
        except Exception as e:
            print(f"Error : {e}")
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
        specific_date = pd.to_datetime('2023-01-15')
        exog_data = pd.DataFrame({'Temperature': [data[0]], 'Humidity': [data[1]], 'SunlightHours': [data[2]]}, index=[specific_date])
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
            conn.commit()

            # Đóng kết nối
            cursor.close()
            conn.close()
            return [email[0] for email in emails]

        except Exception as e:
            print(f"Error fetching emails from database: {e}")
            return []

    def load_model(self):

        with open('model.pkl', 'rb') as pkl:
            self.model_fit = pickle.load(pkl)

    def predict_rain(self, data):
        forecast = self.model_fit.get_forecast(steps=1, exog=data)

        # Lấy dự đoán
        forecast_mean = forecast.predicted_mean.iloc[0]

        # Kiểm tra xem dự đoán có mưa hay không (với ngưỡng là 0.5 hoặc tùy chọn)
        print(forecast_mean)
        if forecast_mean > 0.5:
            return 1
        else:
            return 0
    def save_to_database(self, data, conn):
        try:
            cursor = conn.cursor()
            # Chuẩn bị câu lệnh SQL
            insert_query = """
                INSERT INTO sensor (temperature, temperature_out, humidity, lux, fan_speed, pump_speed, is_light, is_rain,time )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
            """

            data_to_insert = (
                data['temperature'],
                data['temperatureOut'],
                data['humidity'],
                data['lux'],
                data.get('fanSpeed', None),  # Giả sử bạn có trường này trong dữ liệu của mình
                data.get('pumpSpeed', None),  # Tương tự như trên
                data['isLight'],
                data['isRain'],
                data['time']
            )
            print(data)
            # Thực hiện việc chèn dữ liệu
            cursor.execute(insert_query, data_to_insert)
            return

        except Exception as e:
            print(f"Error saving data to database: {e}")
view = AutoView()
view.client.connect("103.77.246.226", 1883, 60)
view.client.loop_forever()