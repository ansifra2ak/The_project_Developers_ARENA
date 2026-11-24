# Automated Reporting and Optimization

## Overview

The script `automation/task2_automation.py` combines
metrics from all five existing project datasets.

## Features

- Automatic dataset discovery
- Project-specific metrics
- Business findings and recommendations
- Consolidated PDF generation
- CSV and Markdown reporting
- Processing time benchmark
- Memory optimization benchmark

## Run Manually

From the main portfolio directory:

```bash
source .venv/bin/activate
python automation/task2_automation.py
```

## Generated Files

- automation/outputs/task2_metrics.csv
- automation/outputs/task2_report.md
- automation/outputs/task2_portfolio_summary.pdf
- automation/outputs/optimization_results.md

## Recurring Execution

The script can be run repeatedly to update reports.
To execute it automatically on a schedule, configure
a scheduler such as cron or macOS launchd.

The script does not install a schedule by itself.

## Important

All inputs are simulated datasets.
Original project CSV files and notebooks are unchanged.
