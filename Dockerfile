FROM python:3.11-slim-buster

# Extra python env
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
CMD ["./process_data.py"]

RUN apt-get update
RUN apt-get install gcc -y

COPY requirements.txt ./
RUN pip install -r requirements.txt
