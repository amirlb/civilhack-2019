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


def point_to_xy(point):
    lat, lng = point
    return (lng * 94051.21245, lat * 111111.11111)


def xy_to_point(xy):
    x, y = xy
    return (y / 111111.11111, x / 94051.21245)


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


def project_stop_on_route(stop, route):
    (x0, y0) = point_to_xy(stop)
    segment_projections = []
    for i in range(len(route) - 1):
        if route[i] == route[i+1]:
            segment_projections.append(route[i])
            continue
        (x1, y1), (x2, y2) = point_to_xy(route[i]), point_to_xy(route[i+1])
        coef = ((x2-x1) * (x0-x1) + (y2-y1) * (y0-y1)) / ((x2-x1)**2 + (y2-y1)**2)
        if coef <= 0:
            projection = (x1, y1)
        elif coef >= 1:
            projection = (x2, y2)
        else:
            projection = (x1 + coef * (x2-x1), y1 + coef * (y2-y1))
        segment_projections.append(xy_to_point(projection))
    best_ind = min(range(len(segment_projections)),
                   key=lambda i: distance(segment_projections[i], stop))
    return best_ind, segment_projections[best_ind]


def generate_walk_instruction(start, end):
    return {
        'instruction': 'walk',
        'meters': distance(start, end),
        'from': start,
        'to': end,
    }


def generate_bus_instruction(line, start_ind, end_ind):
    stops = line['stop_coords']
    start_route_ind, start_route_pt = project_stop_on_route(stops[start_ind], line['shape'])
    end_route_ind, end_route_pt = project_stop_on_route(stops[end_ind], line['shape'])
    return {
        'instruction': 'take bus',
        'line_number': line['short_name'],
        'long_name': line['long_name'],
        'line_alternative': line['alternative'],
        'stops': [
            {'id': stop_code, 'coords': stop_coords}
            for stop_code, stop_coords
            in zip(line['stop_codes'][start_ind : end_ind + 1],
                    line['stop_coords'][start_ind : end_ind + 1])
        ],
        'shape': [start_route_pt] + line['shape'][start_route_ind + 1 : end_route_ind + 1] + [end_route_pt],
    }


def line_matches_query(line, start, end, max_distance):
    stops = line['stop_coords']
    start_ind = min(range(len(stops)), key=lambda i: distance(start, stops[i]))
    end_ind = min(range(len(stops)), key=lambda i: distance(stops[i], end))
    if start_ind is None or end_ind is None or start_ind >= end_ind:
        return None
    if start_ind >= end_ind:
        return None
    if distance(start, stops[start_ind]) > max_distance:
        return None
    if distance(stops[end_ind], end) > max_distance:
        return None

    return [
        generate_walk_instruction(start, stops[start_ind]),
        generate_bus_instruction(line, start_ind, end_ind),
        generate_walk_instruction(stops[end_ind], end)
    ]


@app.route('/query')
def query():
    start = parse_coords(request.args.get('start'))
    end = parse_coords(request.args.get('end'))
    max_distance = int(request.args.get('walk', 400))
    stops = {}
    trips = []
    for route_id, line in all_lines.items():
        instructions = line_matches_query(line, start, end, max_distance)
        if instructions is not None:
            for step in instructions:
                if step['instruction'] == 'take bus':
                    for stop in step['stops']:
                        if stop['id'] not in stops:
                            stops[stop['id']] = {'coords': stop['coords'], 'lines': []}
                        if step['line_number'] not in stops[stop['id']]['lines']:
                            stops[stop['id']]['lines'].append(step['line_number'])
            trips.append(instructions)
    return jsonify(dict(trips=trips, stops=stops))
