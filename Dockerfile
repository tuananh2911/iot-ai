# Sử dụng image Python
FROM python:3.10

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements.txt vào container và cài đặt các thư viện
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Sao chép mã nguồn của dự án vào container
COPY . /app/

# Cài đặt Django (nếu chưa có trong requirements.txt)
RUN pip install django

# Cài đặt thư viện cần thiết khác (nếu cần)
# RUN pip install ...

# Các lệnh khác (nếu cần)
