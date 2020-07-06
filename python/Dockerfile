FROM python:3.8-slim

WORKDIR /usr/src/app
RUN apt update
RUN apt -y install gcc
RUN apt -y install g++
RUN pip install --upgrade cython
RUN pip install nmslib
RUN pip install pybind11
RUN pip install --upgrade pip

RUN mkdir ~/pip/
RUN touch pip.conf


COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN python -m spacy download en


COPY . .

CMD python -m spacy_lemmatizer.start
