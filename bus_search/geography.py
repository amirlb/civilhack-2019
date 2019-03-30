from math import pi, radians, cos, sqrt


EARTH_RADIUS_METERS = 6371000


class Point:
    LATITUDE_DEGREE_METERS = EARTH_RADIUS_METERS * pi / 180

    __slots__ = ('lat', 'lng')

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

    @classmethod
    def longitude_degree_meters(cls, lat):
        return cls.LATITUDE_DEGREE_METERS * cos(radians(lat))

    def to_tuple(self):
        return (self.lat, self.lng)

    @classmethod
    def from_string(cls, coords_str):
        lat, lng = coords_str.split(',')
        return cls(float(lat), float(lng))

    def to_xy(self):
        return (self.lng * self.longitude_degree_meters(self.lat),
                self.lat * self.LATITUDE_DEGREE_METERS)

    @classmethod
    def from_xy(cls, x, y):
        lat = y / cls.LATITUDE_DEGREE_METERS
        lng = x / cls.longitude_degree_meters(lat)
        return cls(lat, lng)

    def distance(self, other):
        x1, y1 = self.to_xy()
        x2, y2 = other.to_xy()
        return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def __eq__(self, other):
        return self.to_tuple() == other.to_tuple()


class Segment:
    def __init__(self, pt1, pt2):
        self.pt1 = pt1
        self.pt2 = pt2

    def project(self, point):
        if self.pt1 == self.pt2:
            return self.pt1

        x0, y0 = point.to_xy()
        x1, y1 = self.pt1.to_xy()
        x2, y2 = self.pt2.to_xy()
        coef = ((x2-x1) * (x0-x1) + (y2-y1) * (y0-y1)) / ((x2-x1)**2 + (y2-y1)**2)
        if coef <= 0:
            return self.pt1
        elif coef >= 1:
            return self.pt2
        else:
            return Point.from_xy(x1 + coef * (x2-x1), y1 + coef * (y2-y1))


class Path:
    def __init__(self, points):
        self.points = points

    def segments(self):
        return (Segment(self.points[i], self.points[i+1])
                for i in range(len(self.points) - 1))

    def to_list(self):
        return [point.to_tuple() for point in self.points]

    def sub_path(self, start, end):
        start_proj, start_ind = self._project_with_index(start)
        end_proj, end_ind = self._project_with_index(end)
        return Path([start_proj] + self.points[start_ind + 1 : end_ind + 1] + [end_proj])

    def _project_with_index(self, point):
        segment_projections = [segment.project(point) for segment in self.segments()]
        best_ind = min(range(len(segment_projections)),
                    key=lambda i: point.distance(segment_projections[i]))
        return segment_projections[best_ind], best_ind
