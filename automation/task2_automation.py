
# ============================================================
# THE DEVELOPERS ARENA - TASK 2
# AUTOMATED REPORTING + DATA PROCESSING OPTIMIZATION
# FIVE PROJECTS | ONE PYTHON FILE
# ============================================================

from pathlib import Path
from datetime import datetime
from time import perf_counter
from xml.sax.saxutils import escape
import csv
import sys

import pandas as pd
import numpy as np

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "automation" / "outputs"
OUTPUT.mkdir(parents=True, exist_ok=True)

DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

PROJECTS = [
    (
        "Supermarket Sales",
        "data-analysis-portfolio",
        "supermarket_sales.csv"
    ),
    (
        "Student Performance",
        "student-performance-analysis",
        "students_cleaned.csv"
    ),
    (
        "Weather Analysis",
        "weather-data-analysis",
        "weather_cleaned.csv"
    ),
    (
        "Healthcare Analysis",
        "healthcare-data-analysis",
        "hospital_cleaned.csv"
    ),
    (
        "Financial Market",
        "financial-market-analysis",
        "market_cleaned.csv"
    )
]

EXCLUDED = {
    ".venv", ".venv-1", ".git",
    "__pycache__", ".ipynb_checkpoints"
}

# ------------------------------------------------------------
# 1. FIND THE EXISTING PROJECT DATASETS
# ------------------------------------------------------------

def find_file(folder_name, filename):
    folder = ROOT / folder_name

    if not folder.is_dir():
        raise FileNotFoundError(
            f"Project directory not found: {folder}"
        )

    matches = [
        p for p in folder.rglob(filename)
        if p.is_file()
        and not EXCLUDED.intersection(p.parts)
    ]

    if not matches:
        raise FileNotFoundError(
            f"Dataset missing: {folder_name}/{filename}"
        )

    matches.sort(
        key=lambda p: (
            "data" not in p.parts,
            len(p.parts),
            str(p)
        )
    )

    return matches[0]


def require(df, columns, project):
    missing = set(columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"{project}: missing columns {sorted(missing)}"
        )


def number(df, column):
    values = pd.to_numeric(
        df[column], errors="coerce"
    )
    return values


# ------------------------------------------------------------
# 2. GENERATE DOMAIN-SPECIFIC STATISTICS
# ------------------------------------------------------------

def analyze_project(name, df):

    metrics = []
    findings = []
    recommendations = []

    if name == "Supermarket Sales":

        require(
            df,
            ["Sales", "Quantity", "Category", "Product"],
            name
        )

        revenue = number(df, "Sales")
        quantity = number(df, "Quantity")

        category_revenue = (
            df.assign(Sales=revenue)
            .groupby("Category")["Sales"]
            .sum()
        )

        top_category = category_revenue.idxmax()

        metrics = [
            ("Sales records", f"{len(df):,}"),
            ("Total revenue", f"INR {revenue.sum():,.2f}"),
            ("Units sold", f"{quantity.sum():,.0f}"),
            ("Average line sale", f"INR {revenue.mean():,.2f}")
        ]

        findings = [
            f"Highest-revenue category: {top_category}.",
            f"Median recorded line sale: "
            f"INR {revenue.median():,.2f}."
        ]

        recommendations = [
            "Review inventory requirements in leading "
            "categories using verified demand data.",
            "Collect cost information before evaluating "
            "category profitability."
        ]

    elif name == "Student Performance":

        require(
            df,
            ["StudentID", "Result", "AverageScore",
             "AttendancePct"],
            name
        )

        score = number(df, "AverageScore")
        attendance = number(df, "AttendancePct")
        pass_rate = df["Result"].eq("Pass").mean() * 100

        metrics = [
            ("Students", f"{len(df):,}"),
            ("Pass rate", f"{pass_rate:.2f}%"),
            ("Average score", f"{score.mean():.2f}"),
            ("Average attendance", f"{attendance.mean():.2f}%")
        ]

        correlation = attendance.corr(score)

        findings = [
            f"Median student score: {score.median():.2f}.",
            f"Attendance-score correlation: "
            f"{correlation:.3f}."
        ]

        recommendations = [
            "Review subject-specific learning support.",
            "Investigate attendance patterns using "
            "additional educational factors."
        ]

    elif name == "Weather Analysis":

        require(
            df,
            ["City", "TemperatureC",
             "RainfallMM", "HumidityPct"],
            name
        )

        temperature = number(df, "TemperatureC")
        rainfall = number(df, "RainfallMM")
        humidity = number(df, "HumidityPct")

        city_temperature = (
            df.assign(TemperatureC=temperature)
            .groupby("City")["TemperatureC"]
            .mean()
        )

        metrics = [
            ("Observations", f"{len(df):,}"),
            ("Average temperature",
             f"{temperature.mean():.2f} C"),
            ("Total rainfall", f"{rainfall.sum():,.2f} mm"),
            ("Average humidity", f"{humidity.mean():.2f}%")
        ]

        findings = [
            f"Warmest city on average: "
            f"{city_temperature.idxmax()}.",
            f"Maximum observed temperature: "
            f"{temperature.max():.2f} C."
        ]

        recommendations = [
            "Compare weather patterns across locations.",
            "Use verified meteorological data for "
            "real operational forecasts."
        ]

    elif name == "Healthcare Analysis":

        require(
            df,
            ["VisitID", "Department",
             "WaitMinutes", "LengthOfStayDays",
             "SatisfactionScore"],
            name
        )

        wait = number(df, "WaitMinutes")
        stay = number(df, "LengthOfStayDays")
        satisfaction = number(df, "SatisfactionScore")

        metrics = [
            ("Hospital visits", f"{len(df):,}"),
            ("Average waiting time",
             f"{wait.mean():.2f} min"),
            ("Average length of stay",
             f"{stay.mean():.2f} days"),
            ("Average satisfaction",
             f"{satisfaction.mean():.2f}/5")
        ]

        department_wait = (
            df.assign(WaitMinutes=wait)
            .groupby("Department")["WaitMinutes"]
            .mean()
        )

        findings = [
            f"Department with highest average waiting "
            f"time: {department_wait.idxmax()}.",
            f"Median waiting time: {wait.median():.2f} min."
        ]

        recommendations = [
            "Monitor department-level waiting times.",
            "Validate operational findings using "
            "real, ethically collected hospital data."
        ]

    elif name == "Financial Market":

        require(
            df,
            ["Ticker", "Date", "Close", "Volume"],
            name
        )

        df = df.copy()

        df["Date"] = pd.to_datetime(
            df["Date"], errors="coerce"
        )

        df["Close"] = number(df, "Close")

        df = (
            df.dropna(subset=["Date", "Close"])
            .sort_values(["Ticker", "Date"])
        )

        returns = (
            df.groupby("Ticker")["Close"]
            .pct_change(fill_method=None)
        )

        volatility = (
            returns.groupby(df["Ticker"])
            .std() * np.sqrt(252) * 100
        )

        metrics = [
            ("Fictional stocks", f"{df['Ticker'].nunique()}"),
            ("Price observations", f"{len(df):,}"),
            ("Mean daily return",
             f"{returns.mean() * 100:.3f}%"),
            ("Mean annual volatility",
             f"{volatility.mean():.2f}%")
        ]

        findings = [
            f"Highest calculated annualized volatility: "
            f"{volatility.idxmax()}.",
            "The price series are fictional and "
            "are not real market observations."
        ]

        recommendations = [
            "Examine returns together with volatility "
            "and drawdown.",
            "Do not use simulated performance for "
            "real investment decisions."
        ]

    return {
        "name": name,
        "rows": len(df),
        "metrics": metrics,
        "findings": findings,
        "recommendations": recommendations
    }


# ------------------------------------------------------------
# 3. ANALYZE ALL FIVE PROJECTS
# ------------------------------------------------------------

print("=" * 65)
print("TASK 2 - AUTOMATED PORTFOLIO REPORTING")
print("=" * 65)

results = []

for name, folder, filename in PROJECTS:

    path = find_file(folder, filename)

    df = pd.read_csv(path, low_memory=False)

    if df.empty:
        raise ValueError(f"{name}: empty dataset")

    result = analyze_project(name, df)
    results.append(result)

    print(f"\n{name}")
    print("Dataset:", path.relative_to(ROOT))

    for label, value in result["metrics"]:
        print(f"  {label}: {value}")


# ------------------------------------------------------------
# 4. SAVE CONSOLIDATED METRICS AS CSV
# ------------------------------------------------------------

csv_path = OUTPUT / "task2_metrics.csv"

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Project", "Metric", "Value"
    ])

    for result in results:
        for metric, value in result["metrics"]:
            writer.writerow([
                result["name"], metric, value
            ])

print("\nMetrics CSV:", csv_path)


# ------------------------------------------------------------
# 5. SAVE CONSOLIDATED MARKDOWN REPORT
# ------------------------------------------------------------

generated_at = datetime.now().strftime(
    "%Y-%m-%d %H:%M"
)

lines = [
    "# Task 2 - Automated Data Analysis Report",
    "",
    f"Generated: {generated_at}",
    "",
    "**Data source:** Simulated educational datasets.",
    "",
    "## Portfolio Summary",
    "",
    f"Projects analyzed: {len(results)}",
    ""
]

for result in results:

    lines.extend([
        f"## {result['name']}",
        "",
        "### Key Metrics",
        ""
    ])

    for label, value in result["metrics"]:
        lines.append(f"- **{label}:** {value}")

    lines.extend([
        "",
        "### Findings",
        ""
    ])

    for finding in result["findings"]:
        lines.append(f"- {finding}")

    lines.extend([
        "",
        "### Recommendations",
        ""
    ])

    for recommendation in result["recommendations"]:
        lines.append(f"- {recommendation}")

    lines.append("")

lines.extend([
    "## Limitations",
    "",
    "- All five datasets are simulated.",
    "- Results are not causal evidence.",
    "- Financial results are not investment advice.",
    "- Healthcare results are not clinical advice.",
    "",
    "## Automation",
    "",
    "Rerunning task2_automation.py regenerates "
    "the consolidated reports from the existing CSV files."
])

markdown_path = OUTPUT / "task2_report.md"

markdown_path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8"
)


# ------------------------------------------------------------
# 6. CREATE A PROFESSIONAL PDF REPORT
# ------------------------------------------------------------

styles = getSampleStyleSheet()

story = [
    Paragraph(
        "Data Analysis Portfolio - Task 2",
        styles["Title"]
    ),
    Paragraph(
        "Automated Multi-Domain Summary Report",
        styles["Heading2"]
    ),
    Paragraph(
        f"Generated: {generated_at}",
        styles["Normal"]
    ),
    Spacer(1, 15),
    Paragraph(
        "This report summarizes five simulated "
        "data analysis projects.",
        styles["Normal"]
    ),
    Spacer(1, 12)
]

for result in results:

    story.append(Paragraph(
        escape(result["name"]),
        styles["Heading2"]
    ))

    rows = [
        ["Metric", "Value"],
        *result["metrics"]
    ]

    table = Table(
        rows,
        colWidths=[240, 250],
        hAlign="LEFT"
    )

    table.setStyle(TableStyle([
        (
            "BACKGROUND", (0, 0), (-1, 0),
            colors.HexColor("#17365D")
        ),
        (
            "TEXTCOLOR", (0, 0), (-1, 0),
            colors.white
        ),
        (
            "ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.white, colors.HexColor("#F1F5F9")]
        ),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("FONTSIZE", (0, 0), (-1, -1), 9)
    ]))

    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Key Findings", styles["Heading3"]
    ))

    for finding in result["findings"]:
        story.append(Paragraph(
            "- " + escape(finding),
            styles["BodyText"]
        ))

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Recommendations", styles["Heading3"]
    ))

    for recommendation in result["recommendations"]:
        story.append(Paragraph(
            "- " + escape(recommendation),
            styles["BodyText"]
        ))

    story.append(Spacer(1, 15))

story.append(Paragraph(
    "Limitations",
    styles["Heading2"]
))

story.append(Paragraph(
    "This report uses simulated educational datasets. "
    "Results must not be treated as actual business, "
    "clinical, financial or meteorological evidence.",
    styles["BodyText"]
))

pdf_path = OUTPUT / "task2_portfolio_summary.pdf"

SimpleDocTemplate(
    str(pdf_path),
    pagesize=A4,
    rightMargin=45,
    leftMargin=45,
    title="Task 2 Automated Portfolio Report",
    author="Data Analysis Portfolio"
).build(story)

print("PDF Report:", pdf_path)
print("Markdown Report:", markdown_path)


# ------------------------------------------------------------
# 7. PERFORMANCE OPTIMIZATION BENCHMARK
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("DATA PROCESSING OPTIMIZATION BENCHMARK")
print("=" * 65)

rng = np.random.default_rng(2026)

N = 30000

benchmark_df = pd.DataFrame({
    "Category": rng.choice(
        ["Groceries", "Electronics",
         "Clothing", "Home", "Books"],
        N
    ),
    "Quantity": rng.integers(1, 10, N),
    "Sales": rng.uniform(100, 5000, N)
})

# Method A: Python row-by-row loop

start = perf_counter()

loop_result = {}

for _, row in benchmark_df.iterrows():
    category = row["Category"]

    loop_result[category] = (
        loop_result.get(category, 0.0)
        + row["Sales"]
    )

loop_time = perf_counter() - start

# Method B: Optimized Pandas groupby

start = perf_counter()

optimized_result = (
    benchmark_df.groupby("Category")["Sales"]
    .sum()
)

optimized_time = perf_counter() - start

# Confirm both methods produce equivalent results

for category, value in optimized_result.items():
    assert np.isclose(
        loop_result[category],
        value,
        rtol=1e-9,
        atol=1e-6
    ), "Optimization results do not match"

speedup = (
    loop_time / optimized_time
    if optimized_time > 0 else float("inf")
)

# Memory usage before optimization

original_memory = benchmark_df.memory_usage(
    deep=True
).sum()

# Demonstrate dtype optimization on a separate copy

optimized_df = benchmark_df.copy()

optimized_df["Category"] = (
    optimized_df["Category"].astype("category")
)

optimized_df["Quantity"] = (
    pd.to_numeric(
        optimized_df["Quantity"],
        downcast="integer"
    )
)

# Float32 reduces memory, but can reduce numeric precision.
optimized_df["Sales"] = (
    optimized_df["Sales"].astype("float32")
)

optimized_memory = optimized_df.memory_usage(
    deep=True
).sum()

memory_reduction = (
    (original_memory - optimized_memory)
    / original_memory * 100
)

print(f"Benchmark records: {N:,}")
print(f"Row-by-row processing: {loop_time:.6f} sec")
print(f"Pandas groupby: {optimized_time:.6f} sec")
print(f"Measured speedup: {speedup:.2f}x")
print(f"Original memory: {original_memory / 1024:.2f} KB")
print(f"Optimized memory: {optimized_memory / 1024:.2f} KB")
print(f"Memory reduction: {memory_reduction:.2f}%")

optimization_report = f"""# Data Processing Optimization Report

Generated: {generated_at}

## Objective

Compare standard row-by-row Python processing
with vectorized Pandas aggregation.

## Benchmark Dataset

- Records: {N:,}
- Categories: 5
- Data type: Simulated

## Performance Results

| Measurement | Result |
|---|---:|
| Row-by-row processing | {loop_time:.6f} seconds |
| Pandas groupby | {optimized_time:.6f} seconds |
| Measured speedup | {speedup:.2f}x |
| Original memory | {original_memory / 1024:.2f} KB |
| Optimized memory | {optimized_memory / 1024:.2f} KB |
| Memory reduction | {memory_reduction:.2f}% |

## Optimization Techniques

1. Replace Python iterrows() aggregation with groupby().
2. Use categorical dtype for repeated text values.
3. Use smaller integer dtypes where safe.
4. Use float32 only when reduced precision is acceptable.
5. Avoid unnecessary copies and repeated calculations.

## Verification

The loop and vectorized group totals were compared
using numerical tolerance.

## Limitations

This is a single local timing run, not a comprehensive
benchmark. Timing varies by hardware and system load.
The memory comparison uses a separately optimized copy,
not the original project datasets.
"""

optimization_path = (
    OUTPUT / "optimization_results.md"
)

optimization_path.write_text(
    optimization_report,
    encoding="utf-8"
)

# ------------------------------------------------------------
# 8. CREATE AUTOMATION DOCUMENTATION
# ------------------------------------------------------------

automation_doc = """# Automated Reporting and Optimization

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
"""

(DOCS / "automation_optimization.md").write_text(
    automation_doc,
    encoding="utf-8"
)

# ------------------------------------------------------------
# 9. LOG SUCCESSFUL EXECUTION
# ------------------------------------------------------------

history_path = OUTPUT / "run_history.log"

with history_path.open(
    "a", encoding="utf-8"
) as f:
    f.write(
        f"{generated_at} | SUCCESS | "
        f"{len(results)} projects analyzed\n"
    )

# ------------------------------------------------------------
# 10. FINAL VERIFICATION
# ------------------------------------------------------------

expected = [
    csv_path,
    markdown_path,
    pdf_path,
    optimization_path,
    history_path
]

for file in expected:
    assert file.is_file() and file.stat().st_size > 0

print("\n" + "=" * 65)
print("TASK 2 AUTOMATION COMPLETED SUCCESSFULLY")
print("=" * 65)

print("Projects analyzed:", len(results))
print("Reports generated:", len(expected))
print("All original datasets preserved.")
print("Results saved in:", OUTPUT)

print("\nNEXT: FINAL PORTFOLIO PRESENTATION")
