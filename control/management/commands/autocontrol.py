import json

import skfuzzy as fuzz
import paho.mqtt.client as mqtt
from skfuzzy import control as ctrl
import numpy as np


class AutoView():
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def adjust_fan_speed(self, outdoor_temp, indoor_temp):
        # Extend the temperature range to -10 to 50 degrees Celsius
        outdoor = ctrl.Antecedent(np.arange(-10, 51, 1), 'outdoor_temperature')
        indoor = ctrl.Antecedent(np.arange(-10, 51, 1), 'indoor_temperature')
        fan_speed = ctrl.Consequent(np.arange(0, 101, 1), 'fan_speed')

        # Define fuzzy sets for outdoor temperature
        # Định nghĩa tập hợp mờ cho nhiệt độ ngoài trời
        outdoor['cold'] = fuzz.trimf(outdoor.universe, [-10, 0, 10])
        outdoor['comfortable'] = fuzz.trimf(outdoor.universe, [18, 24, 30])
        outdoor['hot'] = fuzz.trimf(outdoor.universe, [30, 40, 50])

        # Define fuzzy sets for indoor temperature
        # Định nghĩa tập hợp mờ cho nhiệt độ ngoài trời
        indoor['cold'] = fuzz.trimf(indoor.universe, [-10, 0, 10])
        indoor['comfortable'] = fuzz.trimf(indoor.universe, [18, 30, 30])
        indoor['hot'] = fuzz.trimf(indoor.universe, [30, 40, 50])

        # Define fuzzy sets for fan speed
        fan_speed['off'] = fuzz.trimf(fan_speed.universe, [0, 0, 10])
        fan_speed['low'] = fuzz.trimf(fan_speed.universe, [0, 25, 50])
        fan_speed['medium'] = fuzz.trimf(fan_speed.universe, [25, 50, 75])
        fan_speed['high'] = fuzz.trimf(fan_speed.universe, [50, 75, 100])
        fan_speed['very_high'] = fuzz.trimf(fan_speed.universe, [75, 100, 100])

        # Define rules
        rule0 = ctrl.Rule(outdoor['cold'] | indoor['cold'], fan_speed['off'])
        rule1 = ctrl.Rule(outdoor['cold'] | indoor['comfortable'], fan_speed['off'])
        rule2 = ctrl.Rule(outdoor['cold'] | indoor['hot'], fan_speed['medium'])
        rule3 = ctrl.Rule(outdoor['comfortable'] & indoor['cold'], fan_speed['off'])
        rule4 = ctrl.Rule(outdoor['comfortable'] | indoor['comfortable'], fan_speed['low'])
        rule5 = ctrl.Rule(outdoor['comfortable'] | indoor['hot'], fan_speed['high'])
        rule6 = ctrl.Rule(outdoor['hot'] | indoor['cold'], fan_speed['low'])
        rule7 = ctrl.Rule(outdoor['hot'] | indoor['comfortable'], fan_speed['medium'])
        rule8 = ctrl.Rule(outdoor['hot'] | indoor['hot'], fan_speed['very_high'])
        # Create and run the control system
        fan_control = ctrl.ControlSystem([rule0, rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
        fan = ctrl.ControlSystemSimulation(fan_control)
        # Set input values
        fan.input['outdoor_temperature'] = outdoor_temp
        fan.input['indoor_temperature'] = indoor_temp

        # Compute the result
        fan.compute()

        return fan.output['fan_speed']

    def adjust_pump_speed(self, temperature, humid):
        # Define input variables
        temp = ctrl.Antecedent(np.arange(-10, 51, 1), 'temperature')
        humidity = ctrl.Antecedent(np.arange(0, 101, 1), 'humidity')
        pump_speed = ctrl.Consequent(np.arange(0, 101, 1), 'pump_speed')

        # Define fuzzy sets for temperature (similar to your existing code)
        temp['cold'] = fuzz.trimf(temp.universe, [-10, 0, 20])
        temp['comfortable'] = fuzz.trimf(temp.universe, [20, 24, 32])
        temp['hot'] = fuzz.trimf(temp.universe, [30, 40, 50])
        # Define fuzzy sets for humidity
        humidity['low'] = fuzz.trimf(humidity.universe, [0, 0, 50])
        humidity['medium'] = fuzz.trimf(humidity.universe, [30, 50, 70])
        humidity['high'] = fuzz.trimf(humidity.universe, [50, 75, 100])

        # Define fuzzy sets for pump speed (similar to your existing code)
        pump_speed['off'] = fuzz.trimf(pump_speed.universe, [0, 0, 75])
        pump_speed['low'] = fuzz.trimf(pump_speed.universe, [50, 75, 100])
        pump_speed['medium'] = fuzz.trimf(pump_speed.universe, [75, 125, 150])
        pump_speed['high'] = fuzz.trimf(pump_speed.universe, [125, 150, 175])
        pump_speed['very_high'] = fuzz.trimf(pump_speed.universe, [175, 200, 250])
        # Define rules considering both temperature and humidity
        # Example rules (you should define these based on your specific requirements)
        rule0 = ctrl.Rule(temp['cold'] | humidity['low'], pump_speed['off'])
        rule1 = ctrl.Rule(temp['cold'] | humidity['medium'], pump_speed['off'])
        rule2 = ctrl.Rule(temp['cold'] | humidity['high'], pump_speed['medium'])
        rule3 = ctrl.Rule(temp['comfortable'] & humidity['low'], pump_speed['off'])
        rule4 = ctrl.Rule(temp['comfortable'] | humidity['medium'], pump_speed['low'])
        rule5 = ctrl.Rule(temp['comfortable'] | humidity['high'], pump_speed['high'])
        rule6 = ctrl.Rule(temp['hot'] | humidity['low'], pump_speed['low'])
        rule7 = ctrl.Rule(temp['hot'] | humidity['medium'], pump_speed['medium'])
        rule8 = ctrl.Rule(temp['hot'] | humidity['high'], pump_speed['very_high'])
        # ... additional rules as needed

        # Create and run the control system
        pump_control = ctrl.ControlSystem([rule0, rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
        pump = ctrl.ControlSystemSimulation(pump_control)
        print('humd', humidity)
        # Set input values
        pump.input['temperature'] = temperature
        pump.input['humidity'] = humid

        # Compute the result
        pump.compute()

        return pump.output['pump_speed']

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("topic/data")
        client.subscribe("topic/res_mode")

    # Callback khi nhận được tin nhắn từ server
    def on_message(self, client, userdata, msg):
        print(f"Message received: {msg.topic} {str(msg.payload)}")
        if msg.topic == "topic/data":
            client.publish("topic/mode", json.dumps({"check": 2}))
        # Kiểm tra topic
        if msg.topic == "topic/res_mode":
            data = json.loads(msg.payload)
            print(data)
            is_manual_control = data.get("isManualControl") == "true"
            if is_manual_control:
                return  # Không thực hiện gì nếu là chế độ điều khiển thủ công
        if msg.topic == "topic/res_mode":
            return
        # Tiếp tục xử lý cho các topic khác
        data = json.loads(msg.payload)
        temp_in = data['temperature']
        temp_out = data['temperatureOut']
        humd = data['humidity']
        fan_speed = self.adjust_fan_speed(temp_out, temp_in)
        pump_speed = self.adjust_pump_speed(temp_in, humd)
        lux = data['lux']
        is_light = lux < 50

        publish_data = json.dumps({
            "fanSpeed": round(fan_speed),
            "pumpSpeed": round(pump_speed),
            "isLight": is_light
        })

        client.publish("topic/control", publish_data)


view = AutoView()
view.client.connect("103.77.246.226", 1883, 60)
view.client.loop_forever()
