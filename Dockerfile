#动态瓦片服务发布镜像
FROM tile-base

ADD . /farm_tile

CMD ["gunicorn", "-c", "gunicorn_config.py", "-k", "uvicorn.workers.UvicornWorker", "app:app"]
