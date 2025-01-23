# TODO: Copy .env file from host machine to container's filesystem.
FROM python:3.8

# Set the working directory within the container
WORKDIR /api

# Copy the requirements.txt file into the container at /app
COPY requirements /api/

# Update pip to latest version
RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install -r ./requirements

# Copy the rest of your application's source code to the container
COPY . /api

# Expose the port your app will run on
EXPOSE 5000

# Define the command to run your application
CMD ["python3", "app.py"]
