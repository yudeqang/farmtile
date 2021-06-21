#动态瓦片服务发布镜像
FROM registry.cn-hangzhou.aliyuncs.com/shuxiydq/farm-tile:tilebase

ADD . /farm_tile

CMD ["gunicorn", "-c", "gunicorn_config.py", "-k", "uvicorn.workers.UvicornWorker", "app:app"]
