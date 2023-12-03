import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pickle
data = {
    'time': pd.date_range(start='2023-01-01 08:00:00', periods=10, freq='5S'),
    'temperature': [25, 24, 26, 27, 25, 26, 24, 25, 23, 22],
    'humidity': [80, 82, 78, 75, 77, 79, 80, 82, 85, 87],
    'lux': [1000, 1500, 2000, 1800, 1600, 1400, 1200, 1100, 900, 1000],
    'isRain': [0, 0, 0, 1, 0, 1, 0, 1, 1, 0]
}

# Tạo DataFrame
df = pd.DataFrame(data)
df.set_index('time', inplace=True)
df['rain_shifted'] = df['isRain'].shift(-1)
df.dropna(inplace=True)
print(df)
# Chia dữ liệu
train_size = int(0.8 * len(df))
train_data = df.iloc[:train_size]
test_data = df.iloc[train_size:]

# Xây dựng và huấn luyện mô hình SARIMAX
model = SARIMAX(train_data['rain_shifted'],
                order=(1, 0, 1),
                exog=train_data[['temperature', 'humidity', 'lux']])
model_fit = model.fit()

# Dự đoán
predictions = model_fit.forecast(steps=1, exog=[22,87,1000])
print(predictions)
# with open('sarimax_model.pkl', 'wb') as pkl:
#     pickle.dump(model_fit, pkl)