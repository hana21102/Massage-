FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Streamlit config
ENV PYTHONUNBUFFERED=1
ENV PORT=8501
CMD streamlit run massage_filter_app.py --server.port $PORT --server.address 0.0.0.0
