FROM python:3.11-slim

WORKDIR /app

# Build the frontend first so its dist/ ends up in the image.
# (You can skip this and build dist locally, then COPY it in.)
COPY ../frontend /frontend
RUN cd /frontend && (npm ci || npm install) && npm run build

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
