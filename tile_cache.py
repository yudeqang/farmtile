"""
@author: yudeqiang
@file: tile_cache.py
@time: 2021/06/18
@describe: 
"""
import os
import hashlib
from settings import CACHE_DIR
from tile_cut import make_tile


def cal_file_name(param: str):
    # 计算文件名
    md5 = hashlib.md5()
    md5.update(param.encode())
    return md5.hexdigest()


def save_byte2file(file_name, byte):
    # 保存图片
    with open(file_name, 'wb') as f:
        f.write(byte)


def handler_dir(url):
    base = os.path.basename(url)
    path = os.path.join(CACHE_DIR, os.path.splitext(base)[0])
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def cache_img_byte(url, formula="", bands="", rescale="", color_map="", hillshade="",
                   tile_type="", z="", x="", y="", ndvi=False, scale=1):
    file_name = cal_file_name(
        url + formula + bands + rescale + color_map + hillshade + tile_type + str(x) + str(y) + str(z) + str(
            ndvi) + str(scale))
    file_name += '.png'
    cache_dir = handler_dir(url)
    file_name = os.path.join(cache_dir, file_name)  # 拼接文件名

    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            return f.read()

    img_byte = make_tile.get_tile(url, x=x, y=y, z=z, tile_type='orthophoto', ndvi=ndvi,
                                  formula=formula, bands=bands, color_map=color_map, rescale=rescale)

    if int(z) > 20:  # 大于20层不缓存
        return img_byte

    save_byte2file(file_name, img_byte)
    return img_byte


if __name__ == '__main__':
    cal_file_name('test')
