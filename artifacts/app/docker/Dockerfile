FROM python:3.10-slim
WORKDIR /app
COPY flask/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY flask/ .
EXPOSE 5005
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
CMD ["python", "main.py"]
