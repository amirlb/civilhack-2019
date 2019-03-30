import csv
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress

from geography import Point, Path


app = Flask(__name__)
Compress(app)
CORS(app)


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
        'stop_points': list(map(Point.from_string, row['all_stop_latlon'].split(';'))),
        'shape': Path([Point(lat, lng) for lat, lng in shapes[row['route_id']]]),
    }


def generate_walk_instruction(start, end):
    return {
        'instruction': 'walk',
        'meters': start.distance(end),
        'from': start.to_tuple(),
        'to': end.to_tuple(),
    }


def generate_bus_instruction(line, start_ind, end_ind):
    stops = line['stop_points']
    return {
        'instruction': 'take bus',
        'line_number': line['short_name'],
        'long_name': line['long_name'],
        'line_alternative': line['alternative'],
        'stops': [
            {'id': stop_code, 'coords': stop_point.to_tuple()}
            for stop_code, stop_point
            in zip(line['stop_codes'][start_ind : end_ind + 1],
                   line['stop_points'][start_ind : end_ind + 1])
        ],
        'shape': line['shape'].sub_path(stops[start_ind], stops[end_ind]).to_list(),
    }


def line_matches_query(line, start, end, max_distance):
    stops = line['stop_points']
    start_ind = min(range(len(stops)), key=lambda i: start.distance(stops[i]))
    end_ind = min(range(len(stops)), key=lambda i: stops[i].distance(end))
    if start_ind is None or end_ind is None or start_ind >= end_ind:
        return None
    if start_ind >= end_ind:
        return None
    if start.distance(stops[start_ind]) > max_distance:
        return None
    if stops[end_ind].distance(end) > max_distance:
        return None

    return [
        generate_walk_instruction(start, stops[start_ind]),
        generate_bus_instruction(line, start_ind, end_ind),
        generate_walk_instruction(stops[end_ind], end)
    ]


@app.route('/query')
def query():
    start = Point.from_string(request.args.get('start'))
    end = Point.from_string(request.args.get('end'))
    max_distance = int(request.args.get('walk', 400))
    stops = {}
    trips = []
    for line in all_lines.values():
        instructions = line_matches_query(line, start, end, max_distance)
        if instructions is not None:
            trips.append(instructions)
    for trip in trips:
        for step in trip:
            if step['instruction'] == 'take bus':
                for stop in step['stops']:
                    if stop['id'] not in stops:
                        stops[stop['id']] = {'coords': stop['coords'], 'lines': []}
                    if step['line_number'] not in stops[stop['id']]['lines']:
                        stops[stop['id']]['lines'].append(step['line_number'])
    return jsonify(dict(trips=trips, stops=stops))
