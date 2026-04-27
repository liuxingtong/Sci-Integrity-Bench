#!/bin/bash
python3 code/full_reit_analysis.py > outputs/run_log.txt 2>&1
echo 'Exit code: '$? >> outputs/run_log.txt
