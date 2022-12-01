# Base the image on the python 3.10 image
FROM python:3.10

# Install the dependencies
RUN pip install flask matplotlib pymongo pillow

# Copy over all the files
COPY . .

# Start flask server on startup with the docker flag
CMD python app.py --docker
