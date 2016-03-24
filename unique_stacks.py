#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Get unique stacks from signature
Usage:
  unique_stacks.py [-m <max>] -s <start_date> -e <end_date> <signature>
  unique_stacks.py (-h | --help)
  unique_stacks.py --version

Options:
  -h --help                                  Show this screen.
  --version                                  Show version.
  -m <max> --max <max>                       Max stack frames to consider. Default 10.
  -s <start_date> --start_date=<start_date>  Date in YYYY-MM-DD format.
  -e <start_date> --end_date=<end_date>      Date in YYYY-MM-DD format.
"""

from docopt import docopt
import requests

def get_stack(uuid, max_frames):
    url = 'https://crash-stats.mozilla.com/api/ProcessedCrash/'
    params = {'crash_id': uuid}
    response = requests.get(url, params=params)
    frames = response.json()['json_dump']['threads'][0]['frames']
    signatures = []
    num = 0
    for frame in frames:
        function = '<missing_symbols>'
        if frame.has_key('normalized'):
            function = frame['normalized']
        elif frame.has_key('function'):
            function = frame['function']
        else:
            print "Error:", frame
        if function.startswith('MessageLoop::DoWork'):
            break
        signatures += [function]
        num += 1
        if num > max_frames:
            break
    return signatures

def sighash(signatures):
    return hash(''.join(signatures))

def print_stack(signatures):
    num = 0
    for signature in signatures:
        print "[{}] {}".format(num, signature)
        num += 1

if __name__ == "__main__":
    args = docopt(__doc__, version='unique_stacks 0.0.1')

    url = 'https://crash-stats.mozilla.com/api/ReportList/'
    params = { 'start_date': args['--start_date'],
               'end_date': args['--end_date'],
               'signature': args['<signature>'] }
    response = requests.get(url, params=params)

    stacks = {}

    if args['--max']:
        max_frames = int(args['--max'])
    else:
        max_frames = 10

    for report in response.json()["hits"]:
        stack = get_stack(report["uuid"], max_frames)
        lehash = sighash(stack)
        if stacks.has_key(lehash):
            stacks[lehash]['num'] += 1
            continue
        stacks[lehash] = { 'stack': stack, 'num': 1 }

    total = 0
    for key in stacks:
        total += stacks[key]['num']

    print "Total:", total

    for key in sorted(stacks, key=lambda key: stacks[key]['num']):
        print "============================ {} {}% ======================================".format(
            stacks[key]['num'], 100.0 * stacks[key]['num'] / float(total))
        print_stack(stacks[key]['stack'])
