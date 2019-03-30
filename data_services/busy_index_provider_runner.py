from optparse import OptionParser
from data_services.busy_index_provider import BusyIndexProvider


def main():
    """Run this code to perform a busyness query."""

    parser = OptionParser()

    parser.add_option("-H", "--hour",
                      type=int,
                      help="Current hour (0 <= int <= 23).")
    parser.add_option("-m", "--minutes",
                      type=int,
                      help="Current minutes (0 <= int <= 59)")
    parser.add_option("-f", "--future_minutes",
                      default=60,
                      type=int,
                      help="How many minutes in the future to look.")
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
                      help="Complete filepath to output json.")

    options, _ = parser.parse_args()

    busy_index_provider = BusyIndexProvider(options.input_filepath, options.output_filepath,
                                            options.max_busy_index)

    print("Reading data from {} and saving to {}.".format(options.input_filepath, options.output_filepath))
    busy_index_provider.agg_data_and_save(options.hour, options.minutes, options.future_minutes)
    print("Done.")


if __name__ == '__main__':
    main()
