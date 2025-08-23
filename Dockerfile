FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Install supervisor to run multiple processes
RUN pip install supervisor

# Create supervisor config
RUN echo "[supervisord]\nnodaemon=true\n" > /app/supervisord.conf && \
    echo "[program:main]\ncommand=python3 main.py\n" >> /app/supervisord.conf && \
    echo "[program:httpserver]\ncommand=python3 -m http.server 8080 --directory /app/gui\n" >> /app/supervisord.conf

EXPOSE 8080

CMD ["supervisord", "-c", "/app/supervisord.conf"]
