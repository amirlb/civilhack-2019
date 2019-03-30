import pandas as pd
from datetime import time


class Preprocessor(object):
    def __init__(self, time_resolution_minutes=10, geo_resolution_decimals=3,
                 gps_pings_stuck_threshold=3, n_stuck_buses_threshold=2,
                 max_busy_index=10):
        self.time_resolution_minutes = time_resolution_minutes
        self.geo_resolution_decimals = geo_resolution_decimals
        self.gps_pings_stuck_threshold = gps_pings_stuck_threshold
        self.n_stuck_buses_threshold = n_stuck_buses_threshold
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

    def parse_csv_to_stuck_slices_and_save(self, input_filepath, output_filepath):
        df = self.parse_csv_to_df(input_filepath)
        stuck_slices_df = self.get_stuck_slices_df(df)
        self.save_stuck_slices_data_to_csv(stuck_slices_df, output_filepath)

    def parse_csv_to_df(self, filepath):
        df = pd.read_csv(filepath, usecols=self.all_cols)
        df[self.time_col] = df['time_recorded'].apply(lambda s:
                                                      self._strtime_to_round_time(s, self.time_resolution_minutes))
        df[self.lat_col] = df[self.lat_col].round(self.geo_resolution_decimals)
        df[self.lon_col] = df[self.lon_col].round(self.geo_resolution_decimals)
        return df

    def get_stuck_slices_df(self, df):
        """
        A "slice" is a geo-temporal slice
        If a bus spent at least gps_pings_stuck_threshold minutes at the same slice - it's considered stuck
        """
        stuck_buses_df = pd.DataFrame(df.groupby(self.all_cols).size().reset_index(name=self.gps_pings_col))
        stuck_buses_df = stuck_buses_df[stuck_buses_df[self.gps_pings_col] >= self.gps_pings_stuck_threshold]
        stuck_buses_df = pd.DataFrame(stuck_buses_df.groupby(self.all_cols).first().reset_index())

        # for each time-location slice, get stats for stuck buses
        df_1 = stuck_buses_df.groupby(self.slice_cols)[self.gps_pings_col].sum().reset_index(name=self.total_pings_col)
        df_2 = stuck_buses_df.groupby(self.slice_cols).size().reset_index(name=self.n_buses_col)
        stuck_slices_df = pd.merge(df_1, df_2, on=self.slice_cols, how='inner')

        # keep only slices with at least n_stuck_buses_threshold stuck buses
        stuck_slices_df = stuck_slices_df[stuck_slices_df[self.n_buses_col]
                                          >= self.n_stuck_buses_threshold].reset_index(drop=True)
        stuck_slices_df[self.busy_index_col] = (stuck_slices_df[self.total_pings_col]
                                                // stuck_slices_df[self.n_buses_col])

        # Normalize busy index
        stuck_slices_df[self.busy_index_col] = (stuck_slices_df[self.busy_index_col]
                                                / self.max_busy_index).round(3)

        return stuck_slices_df

    def save_stuck_slices_data_to_csv(self, stuck_slices_df, csv_filepath):
        stuck_slices_df.to_csv(csv_filepath, index=False)

    def _strtime_to_round_time(self, s, n_minutes):
        return time(int(s[0:2]), n_minutes * (int(s[3:5]) // n_minutes), 0)
