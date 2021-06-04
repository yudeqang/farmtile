## 介绍
动态瓦片加载服务
基于folium和rio_tiler

## 使用
- 使用docker
- docker run -P -itd farmtile
- 内部使用gunicorn，如需指定进程数与线程数，指定两个环境变量
    - WORKERS
    - THREADS
    - 默认使用CPU数量
- data文件夹是tif文件的路径，请将tif文件夹挂载到这/farm_tile/data文件夹
- docker run -P -v /home/tifs:/farm_tile/data -itd farmtile

## docker文件说明
Dockerfile是发布使用，基础镜像是Dockerfile.base
Dockerfile.gdal是gdal与python的基础镜像，内置的是gdal2.3.2,python3.7.0

