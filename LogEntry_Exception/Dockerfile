FROM python:3.9-slim-buster
WORKDIR /app
RUN pip install   pandas azure-monitor-query azure-identity azure-core
COPY exception.py /app
CMD ["python", "exception.py"]
