@echo off
echo Starting cluster.py in a new window...
start cmd /k "python cluster.py"
echo cluster.py started. 

echo Starting server.py in a new window...
start cmd /k "python server.py"
echo server.py started.

echo Starting client.py in a new window...
start cmd /k "python client.py"
echo client.py started.

pause
