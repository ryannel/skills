#!/bin/sh
# Copies this case's input files into the run's working folder, and makes it a git repository with one commit.
set -e
cp -R "$(dirname "$0")/files/." .
git init -q -b main
git add -A
git commit -qm "Start"
