#!/usr/bin/python3

import argparse
import mutagen
import requests

parser = argparse.ArgumentParser(
    description="Submit a playlist of tracks to Trackman")
parser.add_argument('playlist', help="A text file with one file per line")
args = parser.parse_args()

with open(args.playlist) as f:
    for line in f:
        path = line.strip()
        track = mutagen.File(path)
        r = requests.post(
            'http://localhost:9090/trackman/api/automation/log',
            data={
                'password': "hackme",
                'title': track.get('title', ''),
                'artist': track.get('artist', ''),
                'album': track.get('album', ''),
                'label': track.get('label', ''),
            })
        r.raise_for_status()
