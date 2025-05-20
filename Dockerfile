FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .

ENV BOOMI_ACCOUNT="" BOOMI_USER="" BOOMI_SECRET=""
EXPOSE 8080

CMD ["boomi-mcp", "--transport", "sse", "--port", "8080"]
