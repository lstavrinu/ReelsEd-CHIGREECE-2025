FROM python:3.10.8
RUN apt-get update && apt-get install -y libgettextpo-dev cmake
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN chown -R :www-data /code
RUN groupadd varwwwusers
RUN adduser www-data varwwwusers
RUN apt-get update && apt-get install -y libpq-dev imagemagick ffmpeg fonts-liberation  && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install --trusted-host pypy.org --trusted-host files.pythonhosted.org -r requirements.txt
COPY policy.xml /etc/ImageMagick-6/policy.xml
