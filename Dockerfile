FROM python:3.11-slim

WORKDIR /app 

COPY requirements.txt .    

RUN pip install --no-cache-dir -r requirements.txt  

#copy full project

COPY . .



CMD ["gunicorn", "manage.py", "runserver", "0.0.0.0:8000"]