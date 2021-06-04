"""
@author: yudeqiang
@file: rio_test.py
@time: 2021/04/12
@describe: 
"""
from rio_tiler.errors import TileOutsideBounds, InvalidFormat
from rio_tiler.mercator import get_zooms
from rio_tiler import main
from rio_tiler.utils import array_to_image, get_colormap, expression, linear_rescale, _chunks, _apply_discrete_colormap, has_alpha_band, \
    non_alpha_indexes
from rio_tiler.profiles import img_profiles
from PIL import Image
# from rest_framework import exceptions
import numpy as np
import rasterio
from .formulas import lookup_formula
from rasterio.enums import ColorInterp
from .hsvblend import hsv_blend
from .hillshade import LightSource
import matplotlib.colors as col
import matplotlib.cm as cm
import os
from io import BytesIO


ZOOM_EXTRA_LEVELS = 2


def color_ndvi(g, r, mask):
    mymap = col.LinearSegmentedColormap.from_list('gndvi', ['#422112', '#724C01', '#CEA712', '#FFA904', '#FDFE00',
                                                            '#E6EC06', '#BACF00',
                                                            '#8BB001', '#72A002', '#5B8D03', '#448102', '#2C7001',
                                                            '#176100', '#035201'], 256)
    cm.register_cmap(cmap=mymap)
    ndvi = (g - r) / (g + r)
    sm = cm.ScalarMappable(cmap=cm.get_cmap('gndvi'))
    sm.set_clim(-0.1, 0.4)
    rgba = sm.to_rgba(ndvi, bytes=True)
    rgba[:, :, 3] = mask
    return rgba


def get_elevation_tiles(elevation, url, x, y, z, tilesize, nodata, resampling, padding):
    tile = np.full((tilesize * 3, tilesize * 3), nodata, dtype=elevation.dtype)

    try:
        left, _ = main.tile(url, x - 1, y, z, indexes=1, tilesize=tilesize, nodata=nodata,
                            resampling_method=resampling, tile_edge_padding=padding)
        tile[tilesize:tilesize*2,0:tilesize] = left
    except TileOutsideBounds:
        pass

    try:
        right, _ = main.tile(url, x + 1, y, z, indexes=1, tilesize=tilesize, nodata=nodata,
                             resampling_method=resampling, tile_edge_padding=padding)
        tile[tilesize:tilesize*2,tilesize*2:tilesize*3] = right
    except TileOutsideBounds:
        pass

    try:
        bottom, _ = main.tile(url, x, y + 1, z, indexes=1, tilesize=tilesize, nodata=nodata,
                              resampling_method=resampling, tile_edge_padding=padding)
        tile[tilesize*2:tilesize*3,tilesize:tilesize*2] = bottom
    except TileOutsideBounds:
        pass

    try:
        top, _ = main.tile(url, x, y - 1, z, indexes=1, tilesize=tilesize, nodata=nodata,
                           resampling_method=resampling, tile_edge_padding=padding)
        tile[0:tilesize,tilesize:tilesize*2] = top
    except TileOutsideBounds:
        pass

    tile[tilesize:tilesize*2,tilesize:tilesize*2] = elevation

    return tile


def rescale_tile(tile, mask, rescale = None):
    if rescale:
        try:
            rescale_arr = list(map(float, rescale.split(",")))
        except ValueError:
            raise Exception("Invalid rescale value")

        rescale_arr = list(_chunks(rescale_arr, 2))
        if len(rescale_arr) != tile.shape[0]:
            rescale_arr = ((rescale_arr[0]),) * tile.shape[0]

        for bdx in range(tile.shape[0]):
            if mask is not None:
                tile[bdx] = np.where(
                    mask,
                    linear_rescale(
                        tile[bdx], in_range=rescale_arr[bdx], out_range=[0, 255]
                    ),
                    0,
                )
            else:
                tile[bdx] = linear_rescale(
                    tile[bdx], in_range=rescale_arr[bdx], out_range=[0, 255]
                )
        tile = tile.astype(np.uint8)

    return tile, mask


def apply_colormap(tile, color_map = None):
    if color_map is not None and isinstance(color_map, dict):
        tile = _apply_discrete_colormap(tile, color_map)
    elif color_map is not None:
        tile = np.transpose(color_map[tile][0], [2, 0, 1]).astype(np.uint8)

    return tile


def get_raster_path():
    return r'E:\browser_download\odm_orthophoto.tif'


def get_zoom_safe(src_dst):
    minzoom, maxzoom = get_zooms(src_dst)
    if maxzoom < minzoom:
        maxzoom = minzoom

    return minzoom, maxzoom


def get_tile(url, formula="" ,bands="", rescale="",color_map="", hillshade="",
        tile_type="", z="", x="", y="", ndvi=False, scale=1):
    """
    Get a tile image
    url: tif路径
    """

    z = int(z)
    x = int(x)
    y = int(y)

    scale = int(scale)
    ext = "PNG"
    driver = "jpeg" if ext == "jpg" else ext

    indexes = None
    nodata = None

    if formula == '': formula = None
    if bands == '': bands = None
    if rescale == '': rescale = None
    if color_map == '': color_map = None
    if hillshade == '' or hillshade == '0': hillshade = None

    try:
        expr, _ = lookup_formula(formula, bands)
    except ValueError as e:
        raise Exception(str(e))

    if tile_type in ['dsm', 'dtm'] and rescale is None:
        rescale = "0,1000"

    if tile_type in ['dsm', 'dtm'] and color_map is None:
        color_map = "gray"

    if tile_type == 'orthophoto' and formula is not None:
        if color_map is None:
            color_map = "gray"
        if rescale is None:
            rescale = "-1,1"

    if nodata is not None:
        nodata = np.nan if nodata == "nan" else float(nodata)
    tilesize = scale * 256

    # url = get_raster_path()  # 获取tif路径

    if not os.path.isfile(url):
        raise FileNotFoundError()

    with rasterio.open(url) as src:
        minzoom, maxzoom = get_zoom_safe(src)
        has_alpha = has_alpha_band(src)
        if z < minzoom - ZOOM_EXTRA_LEVELS or z > maxzoom + ZOOM_EXTRA_LEVELS:
            raise InvalidFormat()

        # Handle N-bands datasets for orthophotos (not plant health)
        if tile_type == 'orthophoto' and expr is None:
            ci = src.colorinterp

            # More than 4 bands?
            if len(ci) > 4:
                # Try to find RGBA band order
                if ColorInterp.red in ci and \
                        ColorInterp.green in ci and \
                        ColorInterp.blue in ci:
                    indexes = (ci.index(ColorInterp.red) + 1,
                               ci.index(ColorInterp.green) + 1,
                               ci.index(ColorInterp.blue) + 1,)
                else:
                    # Fallback to first three
                    indexes = (1, 2, 3,)
            elif has_alpha:
                indexes = non_alpha_indexes(src)

        # Workaround for https://github.com/OpenDroneMap/WebODM/issues/894
        if nodata is None and tile_type == 'orthophoto':
            nodata = 0

    resampling = "nearest"
    padding = 0
    if tile_type in ["dsm", "dtm"]:
        resampling = "bilinear"
        padding = 16

    if expr is not None:
        tile, mask = expression(
            url, x, y, z, expr=expr, tilesize=tilesize, nodata=nodata, tile_edge_padding=padding,
            resampling_method=resampling
        )
    else:
        tile, mask = main.tile(
            url, x, y, z, indexes=indexes, tilesize=tilesize, nodata=nodata, tile_edge_padding=padding,
            resampling_method=resampling
        )

    if color_map:
        try:
            color_map = get_colormap(color_map, format="gdal")
        except FileNotFoundError:
            raise Exception("Not a valid color_map value")

    intensity = None

    if hillshade is not None:
        try:
            hillshade = float(hillshade)
            if hillshade <= 0:
                hillshade = 1.0
        except ValueError:
            raise Exception("Invalid hillshade value")

        if tile.shape[0] != 1:
            raise Exception(
                "Cannot compute hillshade of non-elevation raster (multiple bands found)")

        delta_scale = (maxzoom + ZOOM_EXTRA_LEVELS + 1 - z) * 4
        dx = src.meta["transform"][0] * delta_scale
        dy = -src.meta["transform"][4] * delta_scale

        ls = LightSource(azdeg=315, altdeg=45)

        # Hillshading is not a local tile operation and
        # requires neighbor tiles to be rendered seamlessly
        elevation = get_elevation_tiles(tile[0], url, x, y, z, tilesize, nodata, resampling, padding)
        intensity = ls.hillshade(elevation, dx=dx, dy=dy, vert_exag=hillshade)
        intensity = intensity[tilesize:tilesize * 2, tilesize:tilesize * 2]

    rgb, rmask = rescale_tile(tile, mask, rescale=rescale)
    rgb = apply_colormap(rgb, color_map)

    if intensity is not None:
        # Quick check
        if rgb.shape[0] != 3:
            raise Exception(
                "Cannot process tile: intensity image provided, but no RGB data was computed.")

        intensity = intensity * 255.0
        rgb = hsv_blend(rgb, intensity)

    if ndvi:
        r = rgb[0, :, :].astype(np.float)
        g = rgb[1, :, :].astype(np.float)
        ndvi = color_ndvi(g, r, mask)
        rgb = ndvi[:, :, :3].transpose((2, 0, 1))
        rmask = ndvi[:, :, 3]
        # im = Image.fromarray(ndvi)
        # return (im)

    options = img_profiles.get(driver, {})
    if rgb.shape[0] > 3:
        rmask = rgb[3, :, :]
        rgb = rgb[:3, :, :]
    white_mask = (rgb[0, :, :] == 255) & (rgb[1, :, :] == 255) & (rgb[2, :, :] == 255)
    black_mask = (rgb[0, :, :] == 0) & (rgb[1, :, :] == 0) & (rgb[2, :, :] == 0)
    white_mask = white_mask | black_mask
    shape = rgb.shape
    arr = np.full((4, shape[1], shape[2]), np.uint8(0))
    arr[:3, :, :, ] = rgb[:3, :, :]
    arr[3, :, :][~white_mask] = 255
    arr = arr.transpose((1, 2, 0))
    img = Image.fromarray(arr)
    buf = BytesIO()
    img.save(buf, 'png')
    # img.save('test.png')
    return buf.getvalue()
    # return buf


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import matplotlib.colors as col
    import matplotlib.cm as cm


    def color_ndvi(g, r, mask):
        mymap = col.LinearSegmentedColormap.from_list('gndvi', ['#422112', '#724C01', '#CEA712', '#FFA904', '#FDFE00',
                                                                '#E6EC06', '#BACF00',
                                                                '#8BB001', '#72A002', '#5B8D03', '#448102', '#2C7001',
                                                                '#176100', '#035201'], 256)
        cm.register_cmap(cmap=mymap)
        ndvi = (g - r) / (g + r)
        sm = cm.ScalarMappable(cmap=cm.get_cmap('gndvi'))
        sm.set_clim(-0.1, 0.4)
        rgba = sm.to_rgba(ndvi, bytes=True)
        rgba[:, :, 3] = mask
        return rgba
    x, y, z = 3311151, 1736626, 22
    # 206948&y=108540&z=18 18/206946/108539
    # for i in range(100):
    # res = t.get(x=x,y=y,z=z, formula='GNDVI', bands='RGB',color_map='rdylgn',rescale='-1,1')
    rgb, mask = get_tile(get_raster_path(), x=x,y=y,z=z, tile_type='orthophoto')
    print(rgb.shape)
    r = rgb[0, :, :].astype(np.float)
    g = rgb[1, :, :].astype(np.float)
    ndvi = color_ndvi(g, r, mask)
    # im = Image.fromarray(rgb.transpose((1,2,0)))
    im = Image.fromarray(ndvi)
    im.save("ndvi.png")
    im = Image.fromarray(rgb.transpose((1,2,0)))
    im.save("rgb.png")
    # print(r)
        # print(len(res))
    # with open('test2.png', 'wb') as f:
    #     f.write(res[0])
    # 21/1655572/1228840.png
