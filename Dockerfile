FROM python:3.10

RUN pip install flask matplotlib pymongo pillow

COPY . .

CMD python app.py --docker
