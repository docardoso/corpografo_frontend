FROM zauberzeug/nicegui:latest

expose 8080

workdir /app

COPY . .

CMD ["python3 main.py"]
