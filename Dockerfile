FROM python:3.11.2-slim-bullseye

# set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# set work directory
WORKDIR /code

# install dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Add startup script
COPY app.py app.py

# Set the entry point to your script
ENTRYPOINT ["python3", "app.py"]