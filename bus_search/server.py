import csv
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress

from geography import Point, Path, ApproxCover


app = Flask(__name__)
Compress(app)
CORS(app)


def parse_hour(hour_str):
    parts = hour_str.split(':')
    return sum(int(part) / 60.0**ind for ind, part in enumerate(parts))


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
all_stops = {}
for row in csv.DictReader(open('data/2019-03-20_route_stats.csv')):
    if row['route_id'] not in shapes:
        continue
    line = {
        'short_name': row['route_short_name'],
        'long_name': row['route_long_name'],
        'alternative': row['route_alternative'],
        'start_time': parse_hour(row['start_time']),
        'end_time': parse_hour(row['end_time']),
        'stop_codes': row['all_stop_code'].split(';'),
        'stop_points': list(map(Point.from_string, row['all_stop_latlon'].split(';'))),
        'shape': Path([Point(lat, lng) for lat, lng in shapes[row['route_id']]]),
    }
    all_lines[row['route_id']] = line
    for code, point in zip(line['stop_codes'], line['stop_points']):
        if code not in all_stops:
            all_stops[code] = {'point': point, 'lines': set()}
        all_stops[code]['lines'].add(line['short_name'])
all_stops = [
    {'id': code, 'coords': stop['point'].to_tuple(), 'lines': sorted(stop['lines'])}
    for code, stop in all_stops.items()
]


print('Loading traffic...')
all_busy_data = []
for row in csv.DictReader(open('data/stuck_data.csv')):
    all_busy_data.append({
        'hour': parse_hour(row['time_recorded']),
        'place': Point(float(row['lat']), float(row['lon'])),
        'busy_index': float(row['busy_index']),
    })
for item in json.load(open('data/stuck_data_2.json'))['data']:
    all_busy_data.append({
        'hour': 7.5,
        'place': Point(item['lat'], item['lon']),
        'busy_index': item['busy_index']
    })


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


def get_stops(hour, point, max_distance):
    good_stops = {}
    for route_id, line in all_lines.items():
        if hour is None or line['start_time'] <= hour <= line['end_time']:
            scores = list(map(point.distance, line['stop_points']))
            ind = min(range(len(scores)), key=lambda i: scores[i])
            if scores[ind] <= max_distance:
                good_stops[route_id] = ind
    return good_stops


def two_lines_match_query(line1, line2, start, end, max_distance):
    start_ind = min(range(len(line1['stop_points'])), key=lambda i: start.distance(line1['stop_points'][i]))
    end_ind = min(range(len(line2['stop_points'])), key=lambda i: line2['stop_points'][i].distance(end))
    if start_ind is None or end_ind is None:
        return None
    if start.distance(line1['stop_points'][start_ind]) > max_distance:
        return None
    if line2['stop_points'][end_ind].distance(end) > max_distance:
        return None

    scores = {
        (off_ind, on_ind): off_point.distance(on_point)
        for off_ind, off_point in enumerate(line1['stop_points'])
        for on_ind, on_point in enumerate(line2['stop_points'])
        if start_ind < off_ind and on_ind < end_ind
    }
    off_ind, on_ind = min(scores.keys(), key=lambda pair: scores[pair])
    off_point = line1['stop_points'][off_ind]
    on_point = line2['stop_points'][on_ind]
    if off_point.distance(on_point) > max_distance:
        return None

    walk_between = [] if off_point == on_point else [generate_walk_instruction(off_point, on_point)]

    return [
        generate_walk_instruction(start, line1['stop_points'][start_ind]),
        generate_bus_instruction(line1, start_ind, off_ind)
    ] + walk_between + [
        generate_bus_instruction(line2, on_ind, end_ind),
        generate_walk_instruction(line2['stop_points'][end_ind], end)
    ]


@app.route('/query')
def query():
    start = Point.from_string(request.args.get('start'))
    end = Point.from_string(request.args.get('end'))
    hour = request.args.get('hour')
    if hour is not None:
        hour = parse_hour(hour)
    max_distance = int(request.args.get('walk', 400))
    busy_data_range = int(request.args.get('busy_data_range', 1000))
    trips = []
    start_points = get_stops(hour, start, max_distance)
    end_points = get_stops(hour, end, max_distance)
    for route_id in set(start_points.keys()) & set(end_points.keys()):
        start_ind = start_points[route_id]
        end_ind = end_points[route_id]
        if start_ind < end_ind:
            line = all_lines[route_id]
            stops = line['stop_points']
            trip = [
                generate_walk_instruction(start, stops[start_ind]),
                generate_bus_instruction(line, start_ind, end_ind),
                generate_walk_instruction(stops[end_ind], end)
            ]
            trips.append(trip)
    if request.args.get('allow_swaps'):
        for route_id1 in start_points.keys():
            for route_id2 in end_points.keys():
                if route_id1 == route_id2:
                    continue
                line1 = all_lines[route_id1]
                line2 = all_lines[route_id2]
                instructions = two_lines_match_query(line1, line2, start, end, max_distance)
                if instructions is not None:
                    trips.append(instructions)
    cover = ApproxCover([start, end] + [Point(*point) for trip in trips for step in trip if step['instruction'] == 'take bus' for point in step['shape']],
                        busy_data_range)
    busy_data = [
        {
            'coords': datum['place'].to_tuple(),
            'busy_index': datum['busy_index']
        }
        for datum in all_busy_data
        if (hour or 7) <= datum['hour'] < (hour or 7) + 1 and cover.contains(datum['place'])
    ]
    return jsonify(dict(trips=trips, busy_data=busy_data))


@app.route('/stops')
def stops():
    # optimization hack for live demo
    center = Point(32.1752, 34.9022)
    my_stops = [stop for stop in all_stops if center.distance(Point(*stop['coords'])) < 20000 and any(str(x) in stop['lines'] for x in [149, 231, 349, 567, 561, 249, 148, 5, 29,])]
    MAX_LIMIT = 1000
    offset = int(request.args.get('offset', 0))
    limit = min(MAX_LIMIT, int(request.args.get('limit', 20)))
    return jsonify({
        'data': my_stops[offset : offset + limit],
        'pagination': {'limit': MAX_LIMIT, 'count': len(my_stops)}
    })
