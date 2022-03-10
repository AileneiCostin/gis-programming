import os
from osgeo import ogr, gdal, gdalconst

def print_drivers():
    """Print a list of available drivers."""
    for i in range(ogr.GetDriverCount()):
        driver = ogr.GetDriver(i)
        writeable = driver.TestCapability(ogr.ODrCCreateDataSource)
        print('{0} ({1})'.format(driver.GetName(),
                                 'read/write' if writeable else 'readonly'))
        
def _geom_str(geom):
    """Get a geometry string for printing attributes."""
    if geom.GetGeometryType() == ogr.wkbPoint:
        return 'POINT ({:.3f}, {:.3f})'.format(geom.GetX(), geom.GetY())
    else:
        return geom.GetGeometryName()

def _get_atts(feature, fields, geom):
    """Get attribute values from a feature."""
    data = [feature.GetFID()]
    geometry = feature.geometry()
    if geom and geometry:
        data.append(_geom_str(geometry))
    values = feature.items()
    data += [values[field] for field in fields]
    return data

def _get_layer(lyr_or_fn):
    """Get the datasource and layer from a filename."""
    if type(lyr_or_fn) is str:
        ds = ogr.Open(lyr_or_fn)
        if ds is None:
            raise OSError('Could not open {0}.'.format(lyr_or_fn))
        return ds.GetLayer(), ds
    else:
        return lyr_or_fn, None

def print_attributes(lyr_or_fn, n=None, fields=None, geom=True, reset=True):
    """Print attribute values in a layer.

    lyr_or_fn - OGR layer object or filename to datasource (will use 1st layer)
    n         - optional number of features to print; default is all
    fields    - optional list of case-sensitive field names to print; default
                is all
    geom      - optional boolean flag denoting whether geometry type is printed;
                default is True
    reset     - optional boolean flag denoting whether the layer should be reset
              - to the first record before printing; default is True
    """
    lyr, ds = _get_layer(lyr_or_fn)
    if reset:
        lyr.ResetReading()

    n = n or lyr.GetFeatureCount()
    geom = geom and lyr.GetGeomType() != ogr.wkbNone
    fields = fields or [field.name for field in lyr.schema]
    data = [['FID'] + fields]
    if geom:
        data[0].insert(1, 'Geometry')
    feat = lyr.GetNextFeature()
    while feat and len(data) <= n:
        data.append(_get_atts(feat, fields, geom))
        feat = lyr.GetNextFeature()
    lens = map(lambda i: max(map(lambda j: len(str(j)), i)), zip(*data))
    format_str = ''.join(map(lambda x: '{{:<{}}}'.format(x + 4), lens))
    for row in data:
        try:
            print(format_str.format(*row))
        except UnicodeEncodeError:
            e = sys.stdout.encoding
            print(codecs.decode(format_str.format(*row).encode(e, 'replace'), e))
    print('{0} of {1} features'.format(min(n, lyr.GetFeatureCount()), lyr.GetFeatureCount()))
    if reset:
        lyr.ResetReading()
