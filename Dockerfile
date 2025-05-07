FROM python:3.11-slim

WORKDIR /app
COPY label_to_taint_operator.py .

RUN pip install kopf kubernetes

ENTRYPOINT ["kopf", "run", "--standalone", "label_to_taint_operator.py"]