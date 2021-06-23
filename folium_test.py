"""
@author: yudeqiang
@file: folium_test.py
@time: 2021/04/14
@describe: 
"""
import rasterio
from rasterio import crs
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rio_tiler.mercator import get_zooms
import numpy as np
import folium
import os
from settings import PUBLISH

data_path = '/disk_sdd/塔石正射整幅'


def cal_bound_center(box):
    bbx = np.array(box)
    lng_val = abs(box[0][0] - box[1][0]) / 2
    lat_val = abs(box[0][1] - box[1][1]) / 2
    return np.min(bbx[:, 0]) + lng_val, np.min(bbx[:, 1]) + lat_val


def get_tif_bounds(tif_path, reverse=False):
    with rasterio.open(tif_path) as tif:
        dst_crs = crs.CRS.from_epsg(4326)
        transform = tif.transform
        width = tif.width
        height = tif.height
        if tif.crs != dst_crs:
            transform, width, height = calculate_default_transform(
                tif.crs, dst_crs, tif.width, tif.height, *tif.bounds)
        bounds = [list(transform * (0, 0)), list(transform * (width, height))]
        center = cal_bound_center(bounds)
        center = list(center)
        if reverse:
            center.reverse()
            bounds = [[i[1], i[0]] for i in bounds]
        _, max_zoom = get_zooms(tif)
        return bounds, center, max_zoom+2


def render_html(location, tile_url, max_zoom, **kwargs):
    # http://mt0.google.com/vt/lyrs=s,h&gl=cn&x=97742&y=53533&z=17&s=Galil
    if tile_url.endswith('.tif'):
        t = os.path.basename(tile_url)
        tile_url = t[:-4]
    tile_url = 'http://%s/tiles/%s/{x}/{y}/{z}' % (PUBLISH, tile_url)
    m = folium.Map(location, tiles=tile_url,
                   attr='shuxiTech',
                   zoom_start=16,
                   max_zoom=max_zoom, **kwargs)
    # folium.TileLayer(tiles=tile_url, min_zoom=15, max_zoom=max_zoom, attr='tile', tms=False).add_to(m)
    folium.LayerControl().add_to(m)
    m.add_child(folium.LatLngPopup())
    return m.get_root().render()


def generate_html(tif_path):
    # tif_abs_path = os.path.join(data_path, tif_path)
    bounds, location, max_zoom = get_tif_bounds(tif_path, reverse=True)
    html = render_html(location, tif_path, max_zoom)
    return html


if __name__ == '__main__':
    # a = get_tif_bounds(r'E:\browser_download\odm_orthophoto_1.3g.tif')
    p = 'longyou2021wrj5cm.tif'
    a = generate_html(p)
    with open('ts_tile.html', 'w') as f:
        f.write(a)
