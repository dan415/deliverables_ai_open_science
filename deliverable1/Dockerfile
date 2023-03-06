# syntax=docker/dockerfile:1

FROM python:3.10-alpine
WORKDIR /app

COPY . .
RUN apk update && apk add gcc make\
                          libc-dev \
                          g++ \
                          curl \
                          gfortran openblas-dev lapack-dev \
                          libffi-dev \
                          cmake
RUN pip install -r requirements.txt
CMD ["python", "src/pdf_analysis.py", "--INPUT_PATH", "./input_files", "--OUTPUT_PATH", "./output_files", "--GROBID_CLIENT_CONFIG_PATH", "./config.json"]

