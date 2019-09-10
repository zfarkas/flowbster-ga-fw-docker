FROM python:3-alpine
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 6000
ENTRYPOINT ["python"]
CMD ["looper.py"]
