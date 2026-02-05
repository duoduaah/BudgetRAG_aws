FROM public.ecr.aws/lambda/python:3.10

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --only-binary=:all: pymupdf==1.26.0
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD [ "src.runtime.handler.lambda_handler" ]
