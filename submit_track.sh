#!/bin/sh
PASSWORD=""
TITLE="Call Me Maybe"
ARTIST="Carly Rae Jepsen"

curl -F "password=$PASSWORD" -F "title=$TITLE" -F "artist=$ARTIST" http://127.0.0.1:5000/trackman/automation/submit
