#!/bin/bash
# go.sh LAYOUTS TS STEM : venv (the image's Python refuses pip, PEP 668), then run_pod_split.sh unchanged
cd /root/m && rm -rf psf-os
TZ=Europe/Zurich date
python3 -m venv /root/venv && export PATH=/root/venv/bin:$PATH
bash run_pod_split.sh "$1" "$2" "$3"
echo EXIT $?
TZ=Europe/Zurich date
