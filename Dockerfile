FROM zauberzeug/nicegui:latest

expose 8080

workdir /app

COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["python3 main.py"]
