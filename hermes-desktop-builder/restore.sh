#!/bin/bash
# Run Ada Chat on Linux or Mac
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python3 "$DIR/ada-chat.py"
