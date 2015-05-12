#!/usr/bin/python
# Filename: tasks.py
# coding: utf-8
__author__ = 'jcsh'
__version__ = '1.0.0'

import os
import urllib2
import json
import codecs

wfs_url = 'http://192.168.2.21/arcgis/rest/services/TDLY/XZJX_2013_WGS84/FeatureServer/4'

base_data = '{"f":"pjson","outFields":"XZQDM,XZQMC","where":"1=1"}'

outFields = ['XZQDM', 'XZQMC']

overwrite = False

def log(message):
    print 'log :' + message


def _writeinfo(obj, file):
    if isinstance(obj, dict):
        for key in obj:
            log('writing ' + key)
            file.writelines('{'+key+':\n')
            _writeinfo(obj[key], file)
            file.writelines('}\n')
    elif isinstance(obj, list):
        file.writelines('[')
        for li in obj:
            _writeinfo(li, file)
        file.writelines('],')
    elif isinstance(obj, str):
        file.writelines('"'+str+'"')
    else:
        file.write(obj)

def obj2Str(obj):
    # 处理部分编码问题--unicode转换
    _str = ''
    if isinstance(obj, dict):
        _str += '{'
        for key in obj:
            _str += '"' + key + '":' + obj2Str(obj[key]) + ',\n'
        _str = _str[0:-2] + '}'
    elif isinstance(obj, list):
        _str += '['
        for index in range(len(obj)):
            _str += obj2Str(obj[index]) + ','
        _str = _str[0:-1] + ']'
    elif isinstance(obj, float) or isinstance(obj, int):
        _str += str(obj)
    elif isinstance(obj, str):
        _str += '"'+obj+'"'
    elif isinstance(obj, bool):
        if obj:
            _str += 'true'
        else:
            _str += 'false'
    else:
        _str += str(obj)
    return _str


def writeinto(key, _file):
    filename = key + '.js'
    log('open '+filename)
    # output = codecs.open(filename, 'w', 'utf-8')
    output = open(filename, 'w')    
    tmp = obj2Str(_file)
    _str = 'var gtGeoJson=gtGeoJson||{};gtGeoJson["'+copy(key)+'"]=(function(){return '+tmp+'}())'
    #_str = str(file)
    log('begin write')
    output.write(_str)
    # output.write(codecs.encode(_str, 'utf-8'))
    output.close()
    log('geojson has already been written into ' + filename + ' down')


def write(files):
    for key in files:
        filename = key+'.js'
        if overwrite:
            writeinto(key, files[key])
        else:
            if os.path.isfile(filename):
                log(filename + ' already exist, continue will Overwrite existing file [yes/no]: ')
                ctn = raw_input()
                if ctn in ['', 'y', 'yes', 'Yes', 'YES', 'Y']:
                    writeinto(key, files[key])
                else:
                    log('exit')
            else:
                log('tool will create a new file ' + filename + ' for storing geojson')
                writeinto(key, files[key])


def get(url):
    request = urllib2.Request(url)
    log(url)
    request.add_header("Content-type", "application/json; charset=utf-8")
    log('querying')
    f = urllib2.urlopen(request)
    content = f.read()
    log('transforming result into json')
    rtn = json.loads(content)
    log('transformed')
    return rtn


def copy(obj):
    if isinstance(obj, dict):
        tmp = {}
        for key in obj:
            log('transform ' + key)
            tmp[copy(key)] = copy(obj[key])
    elif isinstance(obj, list):
        tmp = []
        for li in obj:
            tmp.append(copy(li))
    elif isinstance(obj, unicode):
        log('encoding ' + obj)
        tmp = str(obj.encode('utf-8'))
    else:
        tmp = obj
    return tmp


def pointsEqual(a, b):
    for i in range(len(a)):
        if a[i] != b[i]:
            return False
    return True


def closeRing(coordinates):
    if not pointsEqual(coordinates[0], coordinates[len(coordinates)-1]):
        coordinates.append(coordinates[0])
    return coordinates


def ringIsClockwise(ringToTest):
    total = 0
    i = 0
    rL = len(ringToTest)
    pt1 = ringToTest[i]
    for i in range(rL - 1):
        pt2 = ringToTest[i+1]
        total += (pt2[0] - pt1[0])*(pt2[1] + pt1[1])
        pt1 = pt2
    return total >=0


def vertexIntersectsVertex(a1,a2,b1,b2):
        uaT = (b2[0] - b1[0]) * (a1[1] - b1[1]) - (b2[1] - b1[1]) * (a1[0] - b1[0])
        ubT = (a2[0] - a1[0]) * (a1[1] - b1[1]) - (a2[1] - a1[1]) * (a1[0] - b1[0])
        uB  = (b2[1] - b1[1]) * (a2[0] - a1[0]) - (b2[0] - b1[0]) * (a2[1] - a1[1])        
        if uB == 0.0:
            # 无穷大
            return False
        else:            
            ua = uaT/uB
            ub = ubT/uB
            if 0 <= ua and ua <= 1 and 0 <= ub and ub <=1:
                return True
        return False


def arrayIntersectsArray(a, b):
    log('intersects: %d*%d' % (len(a), len(b)))
    for i in range(len(a)-1):
        for j in range(len(b)-1):            
            if vertexIntersectsVertex(a[i], a[i+1],b[j],b[j+1]):
                log('intersects')
                return True
    log('next-->')
    return False


def containPoint(coordinates,point,i,j):
    b1 = coordinates[i][1] <= point[1] and point[1] < coordinates[j][1]
    b2 = coordinates[j][1] <= point[1] and point[1] < coordinates[i][1]
    b3 = b1 or b2
    if coordinates[j][1] == coordinates[i][1]:
        # 无穷大
        b4 = True
    else:
        b4 = point[0] < (coordinates[j][0] - coordinates[i][0]) * (point[1] - coordinates[i][1]) / (coordinates[j][1] - coordinates[i][1]) + coordinates[i][0]
    return b3 and b4
        


def coordinatesContainPoint(coordinates, point):
    contains = False
    i = -1
    l = len(coordinates)
    j = l-1
    while i < l-1:
        i=i+1        
        if containPoint(coordinates, point, i, j):
            contains = not contains
        j = i
    return contains


def coordinatesContainCoordinates(outer, inner):
    intersects = arrayIntersectsArray(outer, inner)
    contains = coordinatesContainPoint(outer, inner[0])
    if not intersects and contains:
        return True
    return False

def convertRingsToGeoJSON(rings):
    outerRings = []
    holes = []
    for _ring in rings:
        ring = closeRing(_ring)
        if len(ring) < 4:
            continue
        if ringIsClockwise(ring):
            # 外环
            polygon = [ring]
            outerRings.append(polygon)
        else:
            # 内环 洞
            holes.append(ring)
    uncontianedHoles = []
    log('contain? %d*%d' % (len(holes),len(outerRings)))
    while len(holes):
        hole = holes.pop()
        contained = False        
        for i in range(len(outerRings)-1,-1,-1):
            # 遍历所有的外环，判断是否包含洞
            log('hole %d outerRings %d' % (len(holes), i))
            outerRing = outerRings[i][0]
            if coordinatesContainCoordinates(outerRing, hole):
                log('contained')
                outerRings[i].append(hole)
                contained = True
                break
        if not contained:
            uncontianedHoles.append(hole)

    while len(uncontianedHoles):
        hole = uncontianedHoles.pop()
        intersects = False
        for i in range(len(outerRings)-1, -1, -1):
            if arrayIntersectsArray(outerRing, hole):
                outerRings[i].append(hole)
                intersects = True
                break

    if(len(outerRings)==1):
        return {
            'type': 'Polygon',
            'coordinates': outerRings[0]
            }
    else:
        return {
            'type': 'MultiPolygon',
            'coordinates':
                outerRings
            }    


def arcgisToGeojson(feature, idAttribute):
    geojson = {}
    keys = feature.keys()
    if 'x' in keys and 'y' in keys:
        geojson['type'] = 'Point'
        geojson['coordinates'] = [feature['x'], feature['y']]
    if 'points' in keys:
        geojson['type'] = 'MultiPoint'
        geojson.coordinates = feature['points']
    if 'paths' in keys:
        if len(feature['paths']) == 1:
            geojson['type'] = 'LineString'
            geojson['coordinates'] = feature['paths'][0]
        else:
            geojson['type'] = 'MultiLineString'
            geojson['coordinates'] = feature['paths']
    if 'rings' in keys:
        geojson = convertRingsToGeoJSON(feature['rings'])
    if 'geometry' in keys or 'attributes' in keys:
        geojson['type'] = 'Feature'
        if 'geometry' in keys:
            geojson['geometry'] = arcgisToGeojson(feature['geometry'], '')
        else:
            geojson['geometry'] = {}
            
        if 'attributes' in keys:
            geojson['properties'] = copy(feature['attributes'])
            if idAttribute in feature['attributes'].keys():
                geojson['id'] = feature['attributes'][idAttribute]
            elif 'OBJECTID' in feature['attributes'].keys():
                geojson['id'] = feature['attributes']['OBJECTID']
            elif 'FID' in feature['attributes'].keys():
                geojson['id'] = feature['attributes']['FID']
            else:
                geojson['id'] = ''
        else:
            geojson['properties'] = {}
    return geojson
        

def response2FeatureCollection(response, sid=''):
    log('transforming response into featureCollection')
    if sid:
        o_id_field = sid
    elif response[u'objectIdFieldName']:
        o_id_field = response[u'objectIdFieldName']
    elif response[u'fields']:
        for filed in response[u'fields']:
            if filed[u'type'] == u'esriFieldTypeOID':
                o_id_field = filed[u'name']
                break
    else:
        o_id_field = u'OBJECTID'
    log('objectIdField '+o_id_field)
    mgfiles = mergeFeatureCollection(response)    
    files = {}    
    for mgkey in mgfiles:
    #    返回arcgis feature
    #    files[mgkey] = copy(mgfiles[mgkey])
        log(mgkey + '--transeforming arcgis feature to geojson')
    #    返回合乎geojson规范的geojson
        files[mgkey] = arcgisToGeojson(mgfiles[mgkey],o_id_field)
        log(mgkey + '--transeformed arcgis feature to geojson')
    return files


def mergeFeatureCollection(fc):
    log('merge featurecollection into several files')
    log('features total %d' % (len(fc['features'])))
    files = {}
    for feature in fc['features']:
        attributes = feature['attributes']
        _id = attributes[outFields[0]]
        if _id in files.keys():            
            fft = files[_id]
            for i in range(1,len(outFields)):
                i
                filed = outFields[i]
                if not fft['attributes'][filed] and attributes[filed]:
                    fft['attributes'][filed] = attributes[filed]
                    log('change ' + filed +' value to ' + attributes[filed])
            geo = feature['geometry']
            fgeo = fft['geometry']
            for key in geo.keys():
                if key == 'rings' and key in fgeo.keys():
                    for ring in geo['rings']:
                        fgeo['rings'].append(ring)
                elif key == 'rings' and key not in fgeo.keys():
                    fgeo['rings'] = geo['rings']
                elif key == 'paths' and key in fgeo.keys():
                    for path in geo['path']:
                        fgeo['paths'].append(path)
                elif key == 'paths' and key not in fgeo.keys():
                    fgeo['paths'] = geo['paths']
                elif key == 'points' and key in fgeo.keys():
                    for point in geo['points']:
                        fgeo['points'].append(point)
                elif key == 'point' and key in fgeo.keys():
                    fgeo['points'] = [fgeo['point'],geo['point']]
                elif key == 'point' and key not in fgeo.keys() and 'points' not in fgeo.keys():
                    fgeo[key] = geo[key]
                elif key == 'point' and key not in fgeo.keys() and 'points' in fgeo.keys():
                    fgeo['points'].append(geo[key])
                else:
                    if isinstance(geo[key],list):
                        if key in fgeo.keys():
                            fgeo[key].append(geo[key])
                        else:
                            fgeo[key] = geo[key]
        else:
            files[_id] = feature
            log('add file ' + _id)
    log('files total %d' % (len(files)))
    return files


def debug():
    wfs_url = 'http://192.168.2.21/arcgis/rest/services/TDLY/XZJX_2013_WGS84/FeatureServer/4'
    outFields = ['XZQDM', 'XZQMC']
    overwrite = True
    response = get(wfs_url+'/query?f=json&where=1=1&outFields=XZQDM,XZQMC')
    files = response2FeatureCollection(response)    
    write(files)
	
	
if __name__ == "__main__":
    print 'tool may overwrite some exists js files, will you authorise? [yes(default)/no ]'
    ctn = raw_input()
    if ctn in ['', 'y', 'yes', 'Yes', 'YES', 'Y']:
        overwrite = True
    response = get(wfs_url+'/query?f=json&where=XZQDM=3202&outFields=XZQDM,XZQMC')
    files = response2FeatureCollection(response)
    # files = mergeFeatureCollection(fc)
    write(files)
