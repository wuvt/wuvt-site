#!/bin/bash

echo "\
-------------------------------------------------------------------------------
wuvt-site development environment
-------------------------------------------------------------------------------"

if [[ "$USE_EMBEDDED_DB" == "1" ]]; then
    export SQLALCHEMY_DATABASE_URI=sqlite:////tmp/wuvt.db

    echo "Embedded database enabled."
    if [[ ! -f /tmp/wuvt.db ]]; then
        echo "No database found; a new one will be created."
        su www-data -s /bin/sh -c 'flask init_embedded_db'
    fi

    echo "-------------------------------------------------------------------------------"
fi

exec $@
