#/bin/sh

autossh -f -M 13000 -N -i .ssh/id_rsa -L 0.0.0.0:3306:localhost:3306 user@server

