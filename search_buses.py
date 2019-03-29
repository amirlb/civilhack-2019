import csv
from flask import Flask, request, jsonify
from flask_cors import CORS
from math import radians, cos, sin, asin, sqrt


app = Flask(__name__)
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


all_lines = {}
for row in csv.DictReader(open('data/2019-03-20_route_stats.csv')):
    all_lines[row['route_id']] = {
        'short_name': row['route_short_name'],
        'long_name': row['route_long_name'],
        'alternative': row['route_alternative'],
        'stop_codes': row['all_stop_code'].split(';'),
        'stop_coords': list(map(parse_coords, row['all_stop_latlon'].split(';'))),
    }


def line_matches_query(line, start, end, max_distance=400):
    stops = line['stop_coords']
    for i, stop in enumerate(stops):
        if distance(start, stop) < max_distance:
            for j in range(i+1, len(stops)):
                if distance(stops[j], end) < max_distance:
                    return True
    return False


@app.route("/query")
def query():
    start = parse_coords(request.args.get('start'))
    end = parse_coords(request.args.get('end'))
    lines = []
    for line in all_lines.values():
        if line_matches_query(line, start, end):
            lines.append({
                'name': f'{line["short_name"]}\n{line["long_name"]}',
                'stops': line['stop_coords'],
            })
    return jsonify(dict(lines=lines))
