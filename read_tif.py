"""
@author: yudeqiang
@file: read_tif.py
@time: 2021/04/14
@describe: 
"""
import rasterio as ro
import argparse
from tile_cut.make_tile import get_tile
from rio_tiler.mercator import get_zooms

# parser = argparse.ArgumentParser(description='Process some integers.')
# parser.add_argument('tif_path', metavar='P', type=str,
#                     help='a tif file`s path')
#
# args = parser.parse_args()
x,y,z = 613142,871066, 20
# try:
# a = get_tile('C841A4AED195EC5D1086387F12F93123_03126B9B1E7BAB4F73CA9570EC830C5E_1618193987_49.tif', x=x, y=y, z=z, tile_type='orthophoto')
# print(a)
#
p = r'/disk_sdd/塔石正射整幅/longyou2021wrj5cm.tif'
# x, y, z = 3311151, 1736626, 22
    # 206948&y=108540&z=18 18/206946/108539
    # for i in range(100):
    # res = t.get(x=x,y=y,z=z, formula='GNDVI', bands='RGB',color_map='rdylgn',rescale='-1,1')
a = get_tile(p, x=x,y=y,z=z, tile_type='orthophoto')
print(a)
# with ro.open('90C6EBBDD0FA25424E8AD0D8D2E49D9E_BC49A81C75FA24C4E79BF0C2F003B5B4_1617757105_33_s.tif') as dst:
#     print(get_zooms(dst))
