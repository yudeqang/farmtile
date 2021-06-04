"""
@author: yudeqiang
@file: app.py
@time: 2021/04/14
@describe: 
"""
import uvicorn
from fastapi import FastAPI, Request, Depends, Path, Response
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from tile_cut import make_tile
import time
from fastapi.staticfiles import StaticFiles
import os
from rio_tiler.errors import TileOutsideBounds, InvalidFormat

# openapi_url=None 完全禁用OpenAPI包括docs
# docs_url=None redoc_url=None 禁用两个文档
app = FastAPI()
# p = '/disk_sdd/塔石正射整幅/longyou2021wrj5cm.tif'
# tif_path = '/home/shuxi/farm_tile/tifs'
tif_path = './data'


# 代理静态文件
# app.mount("/tiffs", StaticFiles(directory="tiffs"), name="tiffs")


# 添加中间件
# app.add_middleware(CustomHeaderMiddleware)

# 创建数据库表，已改为使用alembic做数据库迁移
# models.Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get('/tiles/{name}/{x}/{y}/{z}')
async def retile(name: str = Path(...), x: int = Path(...), y: int = Path(...), z: int = Path(...), ndvi: bool = False,
                 formula: str = '', bands: str = '', color_map: str = '', rescale: str = '', ):
    if not name.endswith('.tif'):
        name = name + '.tif'
    tif_url = os.path.join(tif_path, name)
    if not os.path.exists(tif_url):
        return Response('No such file {}'.format(tif_url), status_code=404)
    try:
        img_byte = make_tile.get_tile(tif_url, x=x, y=y, z=z, tile_type='orthophoto', ndvi=ndvi,
                                      formula=formula, bands=bands, color_map=color_map, rescale=rescale)
    except TileOutsideBounds:
        return Response('outside of bounds', status_code=404)
    except FileNotFoundError:
        return Response(f'file:{tif_url} not found on server', status_code=404)
    except InvalidFormat:
        return Response(f'zoom {z} not support', status_code=404)
    return Response(img_byte, media_type='image/apng')


@app.get('/tif_list')
async def get_random_tile():
    return JSONResponse(os.listdir(tif_path))


@app.get('/test/tiles')
async def get_random_tile():
    import random
    from folium_test import generate_html
    tifs = [i for i in os.listdir(tif_path) if i.endswith('tif')]
    t = random.choice(tifs)
    html = generate_html(os.path.join(tif_path, t))
    return HTMLResponse(html)


# app.include_router(
#     web.router,
#     prefix='/web',
#     tags=["web"],  # 标签，在docs中可以看到
#     # 为此路由中的所有路径依赖注入，但值不会传入到路径操作函数中去。
#     # dependencies=[Depends(web.get_current_active_user)]
#                    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=6060)
