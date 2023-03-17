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

gdal.UseExceptions()

def KML_gen(prod_id, file_path, run_type, ort_report_path, output_path, verbose=False, debug=False):

    ds=gdal.Open(file_path)
    gt=ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    ext=GetExtent(gt,cols-1,rows-1)

    # pixel size, samples, lines
    if debug:
        print gt, cols, rows, ext

    src_srs=osr.SpatialReference()
    src_srs.ImportFromWkt(ds.GetProjection())
    tgt_srs = src_srs.CloneGeogCS()

    geo_ext=ReprojectCoords(ext,src_srs,tgt_srs) 

    # lat/lon of four corners
    if debug:
        print geo_ext

    flight_id = prod_id[:8] if run_type == 'CLASSIC_TYPE' else prod_id[:12]
    CONST_URL_FOR_KML = 'http://aviris.jpl.nasa.gov' if run_type == 'CLASSIC_TYPE' \
				else 'http://prism.jpl.nasa.gov' if run_type == 'PRISM_TYPE' else \
				'http://avirisng.jpl.nasa.gov'
    # ...---... ...---... ...---... ...---... ...---... ...---... ...---... 
    if verbose:
        # read date, utc time, solar elevation, and solar azimuth from ortho_report.txt
        with open(ort_report_path, 'r') as handle:
            for line in handle:
                if line.startswith('mid line year'):
                    year=re.search("\d+",line).group(0)
                if line.startswith('mid line month'):
                    month=re.search("\d+",line).group(0)
                if line.startswith('mid line day'):
                    day=re.search("\d+",line).group(0)
                if line.startswith('mid line utc hour'):
                    utc_hr=re.search("\d+",line).group(0)
                if line.startswith('mid line utc min'):
                    utc_min=re.search("\d+",line).group(0)
                if line.startswith('mid solar elevation'):
                    slr_elev=re.search("\d+\.\d+",line).group(0)
                if line.startswith('mid solar azimuth'):
                    slr_az=re.search("\d+\.\d+",line).group(0)

        date_av = year+'-'+month+'-'+day+'T'+utc_hr+':'+utc_min+':00Z'
	Scene = "_sc01" if run_type == 'CLASSIC_TYPE' else ''

	#pdb.set_trace()
        kml_description='<b>NAME: '+prod_id+Scene+'</b><br>'+date_av+'<br>'+'<a href="'+\
			        CONST_URL_FOR_KML+'/cgi/flights_'+year[2:]+\
			        '.cgi?step=view_flightlog&amp;flight_id='+flight_id+\
			        '" target="_blank">'+'<b>Flight Log '+flight_id+\
			        '</b></a><br><b>NS:</b>'+str(cols)+'<b>NL:</b>'+str(rows)+'<br>'+\
			        '<b>PixelSize:</b>'+str(('%.2f' % gt[1]))+'(m) <br>'+\
			        '<b>Solar Elevation:</b>'+str(('%.2f' % float(slr_elev)))+'<br>'+\
			        '<b>Solar Azimuth:</b>'+str(('%.2f' % float(slr_az)))+'<br>'+\
			        '<a href="'+CONST_URL_FOR_KML+'/aviris_locator/y'+\
			        year[2:]+'_RGB/'+prod_id+Scene+'_RGB.jpeg" target="_blank"><b>View RGB Qlook</b></a>'

        RGB_link = CONST_URL_FOR_KML+'/aviris_locator/y'+year[2:]+'_RGB/'+prod_id+Scene+'_RGB-W200.jpg'
        LL = geo_ext[1]
        LR = geo_ext[2]
        UR = geo_ext[3]
        UL = geo_ext[0]
        # ...---... ...---... ...---... ...---... ...---... ...---... ...---... 
        cmd = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<GroundOverlay>
<name>{} Overlay</name>
<description><![CDATA[
{}
]]></description>
<Icon>
<color>ffffffff</color>
<href>{}</href>
<viewBoundScale>0.75</viewBoundScale>
</Icon>
<TimeStamp>
<when>{}</when>
</TimeStamp>
<gx:LatLonQuad>
<coordinates>
{},{},0.000000
{},{},0.000000
{},{},0.000000
{},{},0.000000
</coordinates>
</gx:LatLonQuad>
</GroundOverlay>
</kml>'''.format(prod_id,kml_description,RGB_link,date_av,LL[0],LL[1],LR[0],LR[1],UR[0],UR[1],UL[0],UL[1])

        # writing KML file
        f=open(output_path,'w')
	f.write(cmd)
        f.close()

# ...---... ...---... ...---... ...---... Return list of corner coordinates from a geotransform
def GetExtent(gt,cols,rows):
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])
	    print px,py
            if debug:
                print x,y
        yarr.reverse()
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
	ort_report_path = sys.argv[4]
	output_path = sys.argv[5]
        KML_gen(prod_id, file_path, run_type, ort_report_path, output_path, verbose=verbose, debug=debug)
