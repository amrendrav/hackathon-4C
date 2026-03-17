#!/bin/bash
cd "$(dirname "$0")/backend"
exec /opt/anaconda3/bin/python3 -m uvicorn main:app --reload --port 8000
