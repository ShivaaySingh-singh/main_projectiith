FROM python:3.11

WORKDIR /app 

COPY requirements.txt .    

RUN pip install -r requirements.txt  

#copy full project

COPY . .



CMD ["gunicorn", "project_portal.wsgi:application", "--bind", "0.0.0.0:8000"]