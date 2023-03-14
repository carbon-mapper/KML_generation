# ...---... ...---... ...---... ...---... ...---... ...---... ...---...
# John W. Chapman
# Generate KML 4-point outline without IDL or ENVI
# ...---... ...---... ...---... ...---... ...---... ...---... ...---...

# ...---... ...---... ...---... ...---... ...---... ...---... ...---...
#requires: ortho-corrected reflectance & ortho report
# ...---... ...---... ...---... ...---... ...---... ...---... ...---...
# License: Apache 2.0 (http://www.apache.org/licenses/)


from osgeo import gdal,ogr,osr
import re
import sys
import pdb
import spectral.io.envi as envi
import numpy as np
import matplotlib.pyplot as plt

gdal.UseExceptions()

def KML_gen(prod_id, file_path, run_type, output_path, verbose=False, debug=False):

    ds=gdal.Open(file_path)
    gt=ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize

    img = envi.open(file_path+'.hdr',file_path)
    cmf=img[:,:,0]
    y_firstlist = []
    y_lastlist = []

    x_list = []
    #Make a list of x and y pixels that are at the boundary along image
    for i in np.arange(0,cols,10):
        y = np.where(cmf[:,i]>-9999.)
        firsty = y[0][0]
        lasty = y[0][-1]
        y_firstlist.append(firsty)
        y_lastlist.append(lasty)
        x_list.append(i)
    x_list.extend(x_list[::-1])
    y_firstlist.extend(y_lastlist[::-1])
    y_list=y_firstlist

    ext=GetExtent(gt,x_list,y_list)
    if debug:
        print(gt, cols, rows, ext)

    src_srs=osr.SpatialReference()
    src_srs.ImportFromWkt(ds.GetProjection())
    tgt_srs = src_srs.CloneGeogCS()

    geo_ext=ReprojectCoords(ext,src_srs,tgt_srs) 

    # lat/lon of four corners
    if debug:
        print(geo_ext)
    # ...---... ...---... ...---... ...---... ...---... ...---... ...---... 
    if verbose:
        cmd_head = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Placemark>
<name>{} Outline</name>
<Icon>
<color>ffffffff</color>
sub<viewBoundScale>0.75</viewBoundScale>
</Icon>
<Polygon>
<tessellate>1</tessellate><outerBoundaryIs><LinearRing>
<coordinates>
'''.format(prod_id)
        cmd_tail='''</coordinates>
</LinearRing></outerBoundaryIs>
</Polygon>
</Placemark>
</kml>'''

        # writing KML file
        f=open(output_path,'w')
        f.write(cmd_head)
        for i in geo_ext:
            f.write(str(i[0])+','+str(i[1])+',0.0\n')
        f.write(cmd_tail)
        f.close()

# ...---... ...---... ...---... ...---... Return list of corner coordinates from a geotransform
def GetExtent(gt,xarr,yarr):
    ext=[]
    xgt = []
    ygt = []
    for px in xarr:
       x=gt[0]+(px*gt[1])
       xgt.append(x)
    for py in yarr:
       y=gt[3]+(py*gt[5])
       ygt.append(y)
    ext=zip(xgt,ygt) 
    return ext

# ...---... ...---... ...---... ...---... Reproject a list of x,y coordinates.
def ReprojectCoords(coords,src_srs,tgt_srs):
    trans_coords=[]
    transform = osr.CoordinateTransformation( src_srs, tgt_srs)
    for x,y in coords:
        x,y,z = transform.TransformPoint(x,y)
        trans_coords.append([x,y])
    return trans_coords

# ...---... ...---... ...---... ...---... 
if __name__ == '__main__':
        verbose = True	
        debug = False
        prod_id = sys.argv[1]
        file_path = sys.argv[2]
        run_type = sys.argv[3]
        output_path = sys.argv[4]
        KML_gen(prod_id, file_path, run_type,  output_path, verbose=verbose, debug=debug)
