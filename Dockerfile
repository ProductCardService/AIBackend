FROM huecker.io/library/python:3.11-slim

WORKDIR /aibackend

COPY . /aibackend

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
