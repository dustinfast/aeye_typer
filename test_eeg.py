#! /usr/bin/env python

import argparse
import time
import numpy as np

from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations


def main():
    parser = argparse.ArgumentParser()
    # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', default=0)
    parser.add_argument('--serial-port', type=str, help='serial port', default='/dev/ttyUSB0')
    parser.add_argument('--other-info', type=str, help='other info', default='')
    parser.add_argument('--streamer-params', type=str, help='other info', default='')
    parser.add_argument('--board-id', type=int, help='board id', default=0)
    parser.add_argument('--log', action='store_true')
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.serial_port = args.serial_port
    params.other_info = args.other_info
    params.timeout = args.timeout

    if(args.log):
        BoardShim.enable_dev_board_logger()
    else:
        BoardShim.disable_board_logger()

    board = BoardShim(args.board_id, params)
    board.prepare_session()

    # board.start_stream() # use this for default options
    board.start_stream(45000, args.streamer_params)
    time.sleep(2)
    # data = board.get_current_board_data(256) # get latest 256 packages or less, doesnt remove them from internal buffer
    data = board.get_board_data() # get all data and remove it from internal buffer
    board.stop_stream()
    board.release_session()

    print(data)
    print(data.shape)


if __name__ == "__main__":
    main()
