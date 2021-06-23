"""
@author: yudeqiang
@file: settings.py
@time: 2021/06/18
@describe: 
"""
import os

TIF_PATH = './data'
CACHE_DIR = TIF_PATH + '/cache'

PUBLISH = os.getenv('PUBLISH', '127.0.0.1:6060')  # 发布ip

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


