FROM python:3.7.2
ENV PYTHONUNBUFFERED 1
RUN mkdir /vibing
COPY . /vibing
WORKDIR /vibing

RUN pip install -r /vibing/deploy_assets/requirements.txt

CMD ["bash", "/vibing/entrypoint.sh"]