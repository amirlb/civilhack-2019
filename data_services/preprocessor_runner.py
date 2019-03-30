from optparse import OptionParser
from data_services.preprocessor import Preprocessor


def main():
    """Run this code to perform pre processing flow."""

    parser = OptionParser()

    parser.add_option("-t", "--time_resolution_minutes",
                      default=10,
                      type=int,
                      help="Number of minutes that define the duration of temporal slice."
                           " Default is 10.")
    parser.add_option("-g", "--geo_resolution_decimals",
                      default=3,
                      type=int,
                      help="Number of decimal points in GPS coordinated that define the radius of geographical slice."
                           " Default is 3.")
    parser.add_option("-s", "--gps_pings_stuck_threshold",
                      default=3,
                      type=int,
                      help="Minimal number of GPS pings in the same geo-temporal slice, above which the bus is stuck."
                           " Default is 3")
    parser.add_option("-b", "--n_stuck_buses_threshold",
                      default=2,
                      type=int,
                      help="Minimal number of buses stuck in the same geo-temporal slice,"
                           " above which the slice is busy."
                           " Default is 2.")
    parser.add_option("-x", "--max_busy_index",
                      default=10,
                      type=int,
                      help="Number of minutes that define the duration of temporal slice."
                           " Default is 10")

    parser.add_option("-i", "--input_filepath",
                      type=str,
                      help="Complete filepath to input csv.")
    parser.add_option("-o", "--output_filepath",
                      type=str,
                      help="Complete filepath to output csv.")

    options, _ = parser.parse_args()

    preprocessor = Preprocessor(options.time_resolution_minutes, options.geo_resolution_decimals,
                                options.gps_pings_stuck_threshold, options.n_stuck_buses_threshold,
                                options.max_busy_index)

    print("Reading data from {} and saving to {}.".format(options.input_filepath, options.output_filepath))
    preprocessor.parse_csv_to_stuck_slices_and_save(options.input_filepath, options.output_filepath)
    print("Done.")


if __name__ == '__main__':
    main()
