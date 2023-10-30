FROM python:3.11.6-alpine3.18
WORKDIR /app
COPY ./ .
RUN pip install -r requirements.txt
EXPOSE 9001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9001"]