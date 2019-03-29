import csv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress
from math import radians, cos, sin, asin, sqrt
import json


app = Flask(__name__)
Compress(app)
CORS(app)


def distance(pt1, pt2):
    """
    Calculate the great circle distance (in meters) between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lat1, lng1 = map(radians, pt1)
    lat2, lng2 = map(radians, pt2)

    # haversine formula 
    dlng = lng2 - lng1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000
    return c * r


def parse_coords(coords_str):
    lat, lng = coords_str.split(',')
    return [float(lat), float(lng)]


print('Loading shapes...')
# shapes = {}
# for row in csv.DictReader(open('data/shapes_dif_20181001-20190320.csv')):
#     route_id = row['route_id']
#     if route_id not in shapes:
#         shapes[route_id] = []
#     shapes[route_id].append((int(row['shape_pt_sequence']), (float(row['shape_pt_lat']), float(row['shape_pt_lon']))))
# shapes = {route_id: [pt for ind, pt in sorted(shape)]
#           for route_id, shape in shapes.items()}
shapes = json.load(open('data/shapes.json'))


print('Loading lines...')
all_lines = {}
for row in csv.DictReader(open('data/2019-03-20_route_stats.csv')):
    if row['route_id'] not in shapes:
        continue
    all_lines[row['route_id']] = {
        'short_name': row['route_short_name'],
        'long_name': row['route_long_name'],
        'alternative': row['route_alternative'],
        'stop_codes': row['all_stop_code'].split(';'),
        'stop_coords': list(map(parse_coords, row['all_stop_latlon'].split(';'))),
        'shape': shapes[row['route_id']],
    }


def line_matches_query(line, start, end, max_distance):
    stops = line['stop_coords']
    start_ind = next((i for i in range(len(stops)) if distance(start, stops[i]) < max_distance), None)
    end_ind = next((i for i in reversed(range(len(stops))) if distance(stops[i], end) < max_distance), None)
    if start_ind is not None and end_ind is not None and start_ind < end_ind:
        return {
            'short_name': line['short_name'],
            'long_name': line['long_name'],
            'alternative': line['alternative'],
            'stops': [
                {'id': stop_code, 'coords': stop_coords}
                for stop_code, stop_coords
                in zip(line['stop_codes'][start_ind : end_ind + 1],
                       line['stop_coords'][start_ind : end_ind + 1])
            ],
            'shape': line['shape'],
        }


@app.route('/query')
def query():
    start = parse_coords(request.args.get('start'))
    end = parse_coords(request.args.get('end'))
    max_distance = int(request.args.get('walk', 400))
    lines = []
    for route_id, line in all_lines.items():
        cut_line = line_matches_query(line, start, end, max_distance)
        if cut_line is not None:
            lines.append({
                'id': route_id,
                'name': f'{cut_line["short_name"]}\n{cut_line["long_name"]}',
                'stops': cut_line['stops'],
                'route': cut_line['shape']
            })
    return jsonify(dict(lines=lines))
