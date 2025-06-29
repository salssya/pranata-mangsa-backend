# Gunakan Python 3.10
FROM python:3.10-slim

# Set direktori kerja di container
WORKDIR /app

# Copy semua file ke container
COPY . .

# Install distutils secara manual (kadang belum include)
RUN apt-get update && apt-get install -y python3-distutils

# Install dependencies dari requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Jalankan aplikasi Flask
CMD ["python", "weather.py", "main.py", "lvq_module.py"]
