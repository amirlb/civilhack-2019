import json
import pandas as pd
from datetime import time


class BusyIndexProvider(object):
    def __init__(self, db_filepath, output_json_filepath,  max_busy_index=10):
        self.db_filepath = db_filepath
        self.output_json_filepath = output_json_filepath
        self.max_busy_index = max_busy_index

        self.time_col = 'time_recorded'
        self.trip_col = 'trip_id_to_date'
        self.lat_col = 'lat'
        self.lon_col = 'lon'
        self.slice_cols = [self.time_col, self.lat_col, self.lon_col]
        self.all_cols = self.slice_cols + [self.trip_col]
        self.gps_pings_col = 'pgs_pings'
        self.total_pings_col = 'total_gps_pings'
        self.n_buses_col = 'n_buses'
        self.busy_index_col = 'busy_index'
        self.lng_col = 'lng'

    def agg_data_and_save(self, base_h, base_m, future_minutes=60):
        stuck_slices_df = self.load_data()
        future_busy_df = self.get_future_busy_df(stuck_slices_df, base_h, base_m, future_minutes)
        future_busy_agg_df = self.get_future_busy_agg_df(future_busy_df)
        self.save_agg_data_to_json(future_busy_agg_df, self.output_json_filepath)

    def load_data(self):
        stuck_slices_df = pd.read_csv(self.db_filepath)
        stuck_slices_df['time_recorded'] = stuck_slices_df['time_recorded'].apply(lambda s: self._strtime_to_time(s))
        return stuck_slices_df

    def get_future_busy_df(self, stuck_slices_df, base_h, base_m, future_minutes):
        limit_m = (base_m + future_minutes) % 60
        limit_h = base_h + ((base_m + future_minutes) // 60)
        future_busy_df = stuck_slices_df[stuck_slices_df[self.time_col].apply(
            lambda t: self._is_in_near_future(t, base_h, base_m, limit_h, limit_m))]
        return future_busy_df

    def get_future_busy_agg_df(self, future_busy_df):
        future_busy_agg_df = future_busy_df.groupby([self.lat_col, self.lon_col]).agg(
            {self.time_col: 'size', self.total_pings_col: 'sum', self.n_buses_col: 'sum'}).reset_index()
        future_busy_agg_df[self.busy_index_col] = (future_busy_agg_df[self.total_pings_col]
                                                   / (future_busy_agg_df[self.n_buses_col]
                                                      * future_busy_agg_df[self.time_col]))

        # Normalize busy index
        future_busy_agg_df[self.busy_index_col] = (future_busy_agg_df[self.busy_index_col]
                                                   / self.max_busy_index).round(3)

        future_busy_agg_df = pd.DataFrame(future_busy_agg_df[[self.lat_col, self.lon_col, self.busy_index_col]])
        future_busy_agg_df.rename(index=str, columns={self.lng_col: self.lon_col})

        return future_busy_agg_df

    def save_agg_data_to_json(self, future_busy_agg_df, json_filepath):
        future_busy_agg_dict = {'data': future_busy_agg_df.to_dict('records')}
        json.dump(future_busy_agg_dict, open(json_filepath, 'w'), indent=4)

    def _strtime_to_time(self, s):
        return time(int(s[0:2]), int(s[3:5]), int(s[6:]))

    def _is_in_near_future(self, input_ts, base_h, base_m, limit_h, limit_m):
        if limit_h < 24:
            return time(base_h, base_m) <= input_ts <= time(limit_h, limit_m)
        else:
            return ((time(base_h, base_m) <= input_ts <= time(23, 59, 59))
                    or (time(0, 0) <= input_ts <= time(limit_h % 24, limit_m)))
