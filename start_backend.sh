#!/bin/bash
cd "$(dirname "$0")/backend"
export ACI_DB_PATH="/Users/amrendravimal/workspace/hackathon/aci.duckdb"
exec /opt/anaconda3/bin/python3 -m uvicorn main:app --reload --port 8000
