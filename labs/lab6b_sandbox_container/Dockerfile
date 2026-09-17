# Lab 6b — image ของ "ห้อง": python + mcp SDK + mcp_server.py เท่านั้น ไม่มี .env ไม่มี API key ไม่มีโค้ด agent
FROM python:3.12-slim
RUN pip install --no-cache-dir "mcp>=1.26,<2" \
 && useradd --create-home --uid 10001 sandbox
WORKDIR /app
COPY mcp_server.py /app/mcp_server.py
USER sandbox
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "/app/mcp_server.py"]
