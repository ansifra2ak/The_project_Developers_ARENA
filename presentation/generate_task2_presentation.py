#!/usr/bin/env python3
"""Create a 12-slide Task 2 portfolio deck from the five EXISTING local projects.

Run at the root of The_project_Developers_ARENA:
    python presentation/generate_task2_presentation.py

Requires: python-pptx, pandas, numpy, Pillow.
This script reads CSV files and existing PNGs; it does not modify project folders.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys
import math

import numpy as np
import pandas as pd
from PIL import Image as PILImage
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "presentation"
OUT.mkdir(exist_ok=True)
OUTPUT_PPTX = OUT / "Task2_Data_Analysis_Portfolio.pptx"
OUTPUT_SOURCES = OUT / "slide_sources.md"
GITHUB_URL = "https://github.com/ansifra2ak/The_project_Developers_ARENA"

PROJECTS = [
    ("Supermarket Sales", "data-analysis-portfolio", "supermarket_sales.csv",
     ["01_category_revenue.png", "02_top_products.png", "03_monthly_revenue.png"]),
    ("Student Performance", "student-performance-analysis", "students_cleaned.csv",
     ["02_subject_performance.png", "01_pass_fail.png", "03_attendance_correlation.png"]),
    ("Weather Analysis", "weather-data-analysis", "weather_cleaned.csv",
     ["01_temperature_trends.png", "02_seasonal_rainfall.png", "03_temperature_heatmap.png"]),
    ("Healthcare Analysis", "healthcare-data-analysis", "hospital_cleaned.csv",
     ["01_department_waiting_times.png", "02_monthly_visits.png", "03_wait_vs_satisfaction.png"]),
    ("Financial Market", "financial-market-analysis", "market_cleaned.csv",
     ["01_normalized_prices.png", "02_rolling_volatility.png", "03_correlation_heatmap.png"]),
]
EXCLUDED = {".venv", ".venv-1", ".git", "__pycache__", ".ipynb_checkpoints"}

# --- Theme -----------------------------------------------------------------
NAVY = RGBColor(15, 23, 42)
NAVY2 = RGBColor(24, 43, 69)
CYAN = RGBColor(2, 132, 199)
TEAL = RGBColor(13, 148, 136)
GOLD = RGBColor(217, 119, 6)
WHITE = RGBColor(255, 255, 255)
PALE = RGBColor(246, 249, 252)
PALE_BLUE = RGBColor(234, 245, 252)
LIGHT = RGBColor(226, 232, 240)
SLATE = RGBColor(71, 85, 105)
TEXT = RGBColor(30, 41, 59)
MUTED = RGBColor(100, 116, 139)
FONT = "Arial"
W, H = 13.333, 7.5


def find_named_file(project_dir: Path, filename: str, required=True) -> Path | None:
    """Find a user's actual file, avoiding virtual environments and duplicate caches."""
    hits = [p for p in project_dir.rglob(filename)
            if p.is_file() and not EXCLUDED.intersection(p.parts)]
    hits.sort(key=lambda p: ("data" not in p.parts and "visualizations" not in p.parts,
                             len(p.parts), str(p)))
    if not hits and required:
        raise FileNotFoundError(
            f"Missing {filename} under {project_dir}\n"
            "Run the corresponding existing project notebook first."
        )
    return hits[0] if hits else None


def required_cols(df, cols, project):
    missing = set(cols) - set(df.columns)
    if missing:
        raise ValueError(f"{project} CSV is missing columns: {sorted(missing)}")


def num(s):
    return pd.to_numeric(s, errors="coerce")


def nice(x, digits=0):
    if pd.isna(x) or not np.isfinite(float(x)):
        return "N/A"
    return f"{x:,.{digits}f}"


def percent(x, digits=1):
    return "N/A" if not np.isfinite(float(x)) else f"{x:.{digits}f}%"


def safe_corr(a, b):
    corr = a.corr(b)
    return float(corr) if pd.notna(corr) else float("nan")


def collect():
    data = {}
    missing = []
    for title, folder, csv_name, png_names in PROJECTS:
        project_dir = ROOT / folder
        if not project_dir.is_dir():
            missing.append(str(project_dir))
            continue
        csv_path = find_named_file(project_dir, csv_name, required=False)
        if csv_path is None:
            missing.append(f"{folder}/.../{csv_name}")
            continue
        chart = None
        for name in png_names:
            chart = find_named_file(project_dir, name, required=False)
            if chart:
                break
        if chart is None:
            missing.append(f"{folder}/.../visualizations/*.png")
            continue
        df = pd.read_csv(csv_path, low_memory=False)
        if df.empty:
            raise ValueError(f"The dataset is empty: {csv_path}")
        available_charts = [p for p in project_dir.rglob("*.png")
                            if p.is_file() and not EXCLUDED.intersection(p.parts)]
        notebooks = [p for p in project_dir.rglob("*.ipynb")
                     if p.is_file() and not EXCLUDED.intersection(p.parts)]
        pdfs = [p for p in project_dir.rglob("*.pdf")
                if p.is_file() and not EXCLUDED.intersection(p.parts)]
        data[title] = {
            "df": df, "csv": csv_path, "chart": chart,
            "charts": sorted(available_charts), "notebooks": sorted(notebooks),
            "pdfs": sorted(pdfs), "folder": folder,
        }
    if missing:
        raise FileNotFoundError(
            "The presentation cannot be built without the actual project sources:\n"
            + "\n".join(" - " + m for m in missing)
        )
    return data


def calculate(data):
    # All numbers are computed from the user's local CSV files at runtime.
    d = data["Supermarket Sales"]["df"].copy()
    required_cols(d, ["Sales", "Quantity", "Category", "Product", "Date"], "Supermarket")
    d["Sales"], d["Quantity"] = num(d["Sales"]), num(d["Quantity"])
    cats = d.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    prods = d.groupby("Product")["Sales"].sum().sort_values(ascending=False)
    revenue = d["Sales"].sum()
    if cats.empty or prods.empty or pd.isna(revenue):
        raise ValueError("Supermarket dataset lacks valid sales/category/product observations.")
    retail = dict(
        kpis=[("Recorded revenue", f"INR {nice(revenue)}"),
              ("Product-line records", f"{len(d):,}"),
              ("Units sold", nice(d["Quantity"].sum())),
              ("Top category share", percent(100 * cats.iloc[0] / revenue))],
        bullets=[f"Highest-revenue category: {cats.index[0]}",
                 f"Highest-revenue product: {prods.index[0]}",
                 f"Average product-line sale: INR {nice(d['Sales'].mean(), 2)}"],
        note="Revenue describes simulated line items, not profit or actual customer demand.",
    )

    d = data["Student Performance"]["df"].copy()
    subjects = ["Mathematics", "Science", "English"]
    required_cols(d, ["Result", "AverageScore", "AttendancePct", *subjects], "Student")
    score, attendance = num(d["AverageScore"]), num(d["AttendancePct"])
    subject_means = d[subjects].apply(num).mean().sort_values(ascending=False)
    pass_rate = 100 * d["Result"].astype(str).eq("Pass").mean()
    student = dict(
        kpis=[("Students", f"{len(d):,}"),
              ("Pass rate", percent(pass_rate)),
              ("Average score", nice(score.mean(), 1)),
              ("Mean attendance", percent(attendance.mean()))],
        bullets=[f"Strongest subject by mean score: {subject_means.index[0]}",
                 f"Attendance-score Pearson r: {nice(safe_corr(attendance, score), 3)}",
                 "Pass rule is the one defined in the project notebook."],
        note="Synthetic student data; observed associations cannot establish causality.",
    )

    d = data["Weather Analysis"]["df"].copy()
    required_cols(d, ["City", "TemperatureC", "RainfallMM", "HumidityPct"], "Weather")
    t, rain, humidity = num(d["TemperatureC"]), num(d["RainfallMM"]), num(d["HumidityPct"])
    t_by_city = d.assign(TemperatureC=t).groupby("City")["TemperatureC"].mean().sort_values(ascending=False)
    rain_by_city = d.assign(RainfallMM=rain).groupby("City")["RainfallMM"].sum().sort_values(ascending=False)
    weather = dict(
        kpis=[("City-day observations", f"{len(d):,}"),
              ("Mean temperature", f"{nice(t.mean(), 1)} °C"),
              ("Mean daily rainfall", f"{nice(rain.mean(), 1)} mm"),
              ("Mean humidity", percent(humidity.mean()))],
        bullets=[f"Warmest city on average: {t_by_city.index[0]}",
                 f"Greatest cumulative recorded rainfall: {rain_by_city.index[0]}",
                 f"Maximum simulated temperature: {nice(t.max(), 1)} °C"],
        note="Simulated daily observations are not a meteorological forecast or climate trend.",
    )

    d = data["Healthcare Analysis"]["df"].copy()
    required_cols(d, ["Department", "WaitMinutes", "LengthOfStayDays", "SatisfactionScore"], "Healthcare")
    wait, los, satisfaction = num(d["WaitMinutes"]), num(d["LengthOfStayDays"]), num(d["SatisfactionScore"])
    dept = d.assign(WaitMinutes=wait).groupby("Department")["WaitMinutes"].mean().sort_values(ascending=False)
    health = dict(
        kpis=[("Simulated visits", f"{len(d):,}"),
              ("Mean waiting time", f"{nice(wait.mean(), 1)} min"),
              ("Mean length of stay", f"{nice(los.mean(), 1)} days"),
              ("Mean satisfaction", f"{nice(satisfaction.mean(), 2)}/5")],
        bullets=[f"Highest mean waiting time: {dept.index[0]}",
                 f"Median waiting time: {nice(wait.median(), 1)} minutes",
                 f"Waiting-satisfaction Pearson r: {nice(safe_corr(wait, satisfaction), 3)}"],
        note="Synthetic operational data; not clinical evidence or medical guidance.",
    )

    d = data["Financial Market"]["df"].copy()
    required_cols(d, ["Ticker", "Date", "Close"], "Finance")
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    d["Close"] = num(d["Close"])
    d = d.dropna(subset=["Date", "Close"]).sort_values(["Ticker", "Date"])
    if d.empty:
        raise ValueError("Financial market dataset contains no usable prices.")
    prices = d.pivot_table(index="Date", columns="Ticker", values="Close", aggfunc="last")
    returns = prices.pct_change(fill_method=None).dropna(how="all")
    vols = returns.std() * math.sqrt(252) * 100
    total_returns = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    finance = dict(
        kpis=[("Fictional tickers", str(d["Ticker"].nunique())),
              ("Price observations", f"{len(d):,}"),
              ("Mean annualized volatility", percent(vols.mean())),
              ("Highest simulated return", percent(total_returns.max()))],
        bullets=[f"Top total-return ticker: {total_returns.idxmax()}",
                 f"Highest-volatility ticker: {vols.idxmax()}",
                 "Volatility annualization assumes 252 trading days."],
        note="Fictional securities, no costs or taxes; not investment advice.",
    )
    return [retail, student, weather, health, finance]


def rect(slide, x, y, w, h, color, rounded=False, line=None, lw=1):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(lw)
    return shape


def txt(slide, s, x, y, w, h, size=16, bold=False, color=TEXT,
        align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_after = Pt(0)
    run = p.add_run()
    run.text = str(s)
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return tb


def page(prs, n, label, title, subtitle=""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, W, H, WHITE)
    rect(s, 0, 0, W, 0.115, NAVY)
    txt(s, label.upper(), 0.56, 0.28, 12.2, 0.28, 10, True, TEAL)
    txt(s, title, 0.55, 0.62, 12.2, 0.58, 28, True, NAVY)
    if subtitle:
        txt(s, subtitle, 0.57, 1.23, 12.05, 0.34, 11.5, False, SLATE)
    rect(s, 0.55, 7.09, 12.22, 0.012, LIGHT)
    txt(s, "THE DEVELOPERS ARENA  ·  DATA ANALYSIS PORTFOLIO  ·  SIMULATED DATA",
        0.57, 7.13, 10.8, 0.21, 8, False, MUTED)
    txt(s, f"{n:02d} / 12", 11.6, 7.13, 1.14, 0.21, 9, True, SLATE, PP_ALIGN.RIGHT)
    return s


def fit_image(slide, path, x, y, w, h):
    with PILImage.open(path) as im:
        iw, ih = im.size
    if not iw or not ih:
        return
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    slide.shapes.add_picture(str(path), Inches(x + (w - dw) / 2),
                             Inches(y + (h - dh) / 2),
                             width=Inches(dw), height=Inches(dh))


def chart_card(slide, path, x, y, w, h, caption):
    rect(slide, x, y, w, h, WHITE, rounded=True, line=LIGHT)
    fit_image(slide, path, x + 0.18, y + 0.18, w - 0.36, h - 0.64)
    txt(slide, caption, x + 0.24, y + h - 0.37, w - 0.48, 0.2,
        10, True, SLATE)


def kpi(slide, x, y, w, title, value):
    rect(slide, x, y, w, 0.96, PALE, rounded=True, line=LIGHT)
    txt(slide, title.upper(), x + 0.15, y + 0.10, w - 0.3, 0.21, 9, True, SLATE)
    txt(slide, value, x + 0.13, y + 0.34, w - 0.25, 0.42, 18.5, True, NAVY)


def project_slide(prs, idx, name, number, detail, chart_path, accent):
    s = page(prs, number, f"Project {idx}  ·  {name}", name,
             "Data preparation  →  descriptive analysis  →  visualization  →  interpretation")
    x0 = 0.57
    for j, (lab, value) in enumerate(detail["kpis"]):
        kpi(s, x0 + (j % 2) * 2.13, 1.75 + (j // 2) * 1.10,
            2.02, lab, value)
    rect(s, 0.57, 4.10, 4.18, 2.40, PALE_BLUE, rounded=True)
    txt(s, "KEY FINDINGS", 0.78, 4.25, 3.8, 0.24, 10, True, accent)
    for j, item in enumerate(detail["bullets"]):
        txt(s, "• " + item, 0.78, 4.59 + j * 0.53, 3.75, 0.49,
            11, False, TEXT, valign=MSO_ANCHOR.TOP)
    chart_card(s, chart_path, 4.95, 1.75, 7.80, 4.75,
               "Existing chart from the corresponding project")
    txt(s, detail["note"], 0.58, 6.62, 12.0, 0.30, 9.5, False, MUTED)
    return s


def pill(slide, x, y, w, text, accent):
    rect(slide, x, y, w, 0.42, PALE_BLUE, rounded=True)
    txt(slide, text, x + 0.07, y + 0.05, w - 0.14, 0.30, 10, True, accent,
        PP_ALIGN.CENTER)


def main():
    if ROOT.name != "The_project_Developers_ARENA":
        raise SystemExit(f"Wrong folder: {ROOT}\nPlace this file in ROOT/presentation/ and run it there.")

    project_data = collect()
    details = calculate(project_data)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    prs.core_properties.title = "Task 2 | Multi-Domain Data Analysis Portfolio"
    prs.core_properties.subject = "Five simulated-data analysis projects"
    prs.core_properties.author = "Data Analysis Portfolio"
    prs.core_properties.keywords = "Python, Pandas, Jupyter, visualization, Streamlit"

    # Slide 1 - Title
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, W, H, NAVY)
    rect(s, 0.6, 0.72, 0.10, 5.75, CYAN)
    txt(s, "THE DEVELOPERS ARENA  ·  TASK 2", 0.98, 0.91, 10.3, 0.40, 15, True, RGBColor(125, 211, 252))
    txt(s, "DATA ANALYSIS &\nVISUALIZATION", 0.95, 1.58, 11.3, 1.70, 40, True, WHITE)
    txt(s, "A five-project portfolio across retail, education, weather, healthcare and finance",
        0.99, 3.46, 11.2, 0.84, 18, False, LIGHT)
    for i, name in enumerate(["RETAIL", "EDUCATION", "WEATHER", "HEALTHCARE", "FINANCE"]):
        pill(s, 0.98 + i * 2.34, 4.68, 2.15, name, NAVY)
    txt(s, "PYTHON  ·  PANDAS  ·  STATISTICS  ·  STREAMLIT  ·  REPORTING",
        1.0, 5.55, 11.3, 0.36, 12, True, WHITE)
    txt(s, "ALL DATASETS SIMULATED  •  Generated from existing local project files",
        1.0, 6.78, 11.4, 0.33, 10, False, RGBColor(186, 230, 253))

    # Slide 2 - Overview
    s = page(prs, 2, "Executive overview", "Five domains. One end-to-end workflow.",
             "Existing notebook analyses, reports and visualization outputs")
    names = [p[0] for p in PROJECTS]
    colors = [CYAN, TEAL, GOLD, RGBColor(124, 58, 237), RGBColor(220, 38, 38)]
    for i, (name, clr) in enumerate(zip(names, colors)):
        y = 1.83 + i * 0.87
        rect(s, 0.72, y, 8.15, 0.70, PALE, rounded=True)
        rect(s, 0.72, y, 0.10, 0.70, clr)
        txt(s, f"0{i + 1}", 1.02, y + 0.17, 0.5, 0.30, 13, True, clr)
        txt(s, name, 1.66, y + 0.15, 6.8, 0.34, 16, True, NAVY)
    total_nbs = sum(len(v["notebooks"]) for v in project_data.values())
    total_pdfs = sum(len(v["pdfs"]) for v in project_data.values())
    total_charts = sum(len(v["charts"]) for v in project_data.values())
    for i, (lab, val) in enumerate([
        ("PROJECTS", "05"), ("NOTEBOOK FILES", str(total_nbs)),
        ("PDF REPORTS", str(total_pdfs)), ("CHART IMAGES", str(total_charts))
    ]):
        y = 1.82 + i * 1.13
        rect(s, 9.12, y, 3.5, 0.97, PALE_BLUE, rounded=True)
        txt(s, val, 9.37, y + 0.10, 1.05, 0.62, 28, True, NAVY)
        txt(s, lab, 10.53, y + 0.28, 1.90, 0.28, 10, True, SLATE)
    txt(s, "File counts are detected at generation time; they are not a substitute for execution testing.",
        0.73, 6.44, 11.88, 0.35, 10, False, MUTED)

    # Slide 3 - Methodology
    s = page(prs, 3, "Technical workflow", "From raw CSV to actionable analysis",
             "Consistent methodology implemented with Python and Jupyter")
    steps = [("01", "INGEST", "Load CSV and inspect schema"),
             ("02", "VALIDATE", "Check missing and invalid values"),
             ("03", "TRANSFORM", "Feature engineering and groupby"),
             ("04", "ANALYZE", "Statistics and trend analysis"),
             ("05", "VISUALIZE", "Charts that answer questions"),
             ("06", "REPORT", "PDF, Markdown and exports")]
    for j, (n, label, subtitle) in enumerate(steps):
        c = j % 3
        r = j // 3
        x, y = 0.75 + c * 4.24, 1.97 + r * 2.10
        rect(s, x, y, 3.87, 1.69, PALE, rounded=True, line=LIGHT)
        txt(s, n, x + 0.2, y + 0.13, 0.65, 0.38, 21, True, CYAN)
        txt(s, label, x + 0.97, y + 0.14, 2.56, 0.37, 16, True, NAVY)
        txt(s, subtitle, x + 0.22, y + 0.74, 3.40, 0.64, 13, False, SLATE)
    txt(s, "Technology stack: Pandas • NumPy • SciPy • Matplotlib • Seaborn • Jupyter • ReportLab • Streamlit • Plotly",
        0.76, 6.43, 12.05, 0.33, 10.5, False, MUTED)

    # Slides 4-8 - Project deep dives
    accents = [CYAN, TEAL, GOLD, RGBColor(124, 58, 237), RGBColor(220, 38, 38)]
    for i, ((name, _, _, _), detail, clr) in enumerate(zip(PROJECTS, details, accents), start=1):
        project_slide(prs, i, name, 3 + i, detail, project_data[name]["chart"], clr)

    # Slide 9 - Statistics, testing, data quality
    s = page(prs, 9, "Analytical rigor", "Statistical methods & data quality",
             "Explain methods, assumptions and what the results can and cannot support")
    rect(s, 0.65, 1.78, 5.86, 4.92, PALE, rounded=True)
    txt(s, "METHODS APPLIED", 0.89, 2.01, 5.1, 0.38, 15, True, NAVY)
    for i, item in enumerate([
        "Mean, median, standard deviation, quartiles",
        "Grouped summaries and time-series trends",
        "Pearson correlation for selected comparisons",
        "Welch t-tests in domain notebooks",
        "Returns, volatility and drawdown in finance",
    ]):
        txt(s, "• " + item, 0.91, 2.57 + 0.72 * i, 5.08, 0.54, 12, False, TEXT)
    rect(s, 6.76, 1.78, 5.86, 4.92, PALE_BLUE, rounded=True)
    txt(s, "QUALITY & INTERPRETATION", 7.00, 2.01, 5.18, 0.38, 15, True, NAVY)
    for i, item in enumerate([
        "Verify identifiers and field completeness",
        "Handle out-of-range values explicitly",
        "Distinguish line records from shopping baskets",
        "Avoid causation claims from correlation",
        "Label all synthetic findings and limitations",
    ]):
        txt(s, "• " + item, 7.02, 2.57 + 0.72 * i, 5.07, 0.54, 12, False, TEXT)

    # Slide 10 - Chart gallery
    s = page(prs, 10, "Visualization portfolio", "Five domains, five real project charts",
             "Images are embedded from the existing visualizations/ folders")
    positions = [(0.63, 1.80, 3.95, 2.20), (4.71, 1.80, 3.95, 2.20),
                 (8.79, 1.80, 3.95, 2.20), (2.66, 4.27, 3.95, 2.20),
                 (6.75, 4.27, 3.95, 2.20)]
    for (name, _, _, _), (x, y, w, h) in zip(PROJECTS, positions):
        chart_card(s, project_data[name]["chart"], x, y, w, h, name)

    # Slide 11 - Dashboard & automated reporting
    s = page(prs, 11, "Beyond the notebook", "Interactive dashboard & automated reporting",
             "Portfolio integration and operational delivery")
    dashboard_file = ROOT / "dashboard" / "app.py"
    automation_file = ROOT / "automation" / "task2_automation.py"
    output_pdf = ROOT / "automation" / "outputs" / "task2_portfolio_summary.pdf"
    optim = ROOT / "automation" / "outputs" / "optimization_results.md"
    rect(s, 0.69, 1.83, 5.92, 4.96, PALE, rounded=True)
    txt(s, "INTERACTIVE DASHBOARD", 0.95, 2.05, 5.35, 0.38, 15, True, CYAN)
    txt(s, "Streamlit + Plotly", 0.95, 2.58, 5.08, 0.35, 20, True, NAVY)
    for i, item in enumerate([
        "Switch between all five project domains",
        "Filter records and date ranges",
        "Inspect interactive charts and KPIs",
        "Download filtered datasets as CSV",
    ]):
        txt(s, "• " + item, 0.96, 3.19 + i * 0.62, 5.06, 0.51, 12, False, TEXT)
    txt(s, "SOURCE: dashboard/app.py" if dashboard_file.exists() else "DASHBOARD FILE NOT FOUND",
        0.96, 6.18, 5.12, 0.32, 9.5, True, TEAL if dashboard_file.exists() else GOLD)
    rect(s, 6.79, 1.83, 5.85, 4.96, PALE_BLUE, rounded=True)
    txt(s, "AUTOMATION & EFFICIENCY", 7.05, 2.05, 5.34, 0.38, 15, True, TEAL)
    txt(s, "Repeatable reports", 7.05, 2.58, 5.16, 0.35, 20, True, NAVY)
    for i, item in enumerate([
        "Combine metrics from five project CSVs",
        "Regenerate PDF + CSV + Markdown outputs",
        "Benchmark Python loops against Pandas groupby",
        "Document memory reduction with dtype changes",
    ]):
        txt(s, "• " + item, 7.06, 3.19 + i * 0.62, 5.13, 0.51, 12, False, TEXT)
    if optim.exists():
        body = optim.read_text(encoding="utf-8", errors="replace")
        speedup = re.search(r"Measured speedup\s*\|\s*([^|\n]+)", body)
        reduction = re.search(r"Memory reduction\s*\|\s*([^|\n]+)", body)
        if speedup or reduction:
            benchmark = "  •  ".join(v.group(1).strip() for v in (speedup, reduction) if v)
            txt(s, "Local benchmark: " + benchmark, 7.05, 6.16, 5.25, 0.43, 9.5, True, TEAL)
    elif automation_file.exists():
        txt(s, "Automation script available; benchmark not yet generated", 7.05, 6.15, 5.17, 0.38, 9.5, False, GOLD)
    if output_pdf.exists():
        txt(s, "Consolidated PDF verified as a file", 7.05, 6.58, 5.22, 0.26, 9, False, MUTED)

    # Slide 12 - Closing
    s = page(prs, 12, "Closing summary", "A reproducible, multi-domain portfolio",
             "Five clearly documented simulated-data projects")
    rect(s, 0.75, 1.89, 11.87, 2.02, NAVY, rounded=True)
    txt(s, "WHAT THIS PORTFOLIO DEMONSTRATES", 1.13, 2.18, 10.99, 0.38, 12, True, RGBColor(125, 211, 252))
    txt(s, "Data cleaning  ·  statistical thinking  ·  visual storytelling  ·  reporting",
        1.12, 2.78, 11.0, 0.68, 22, True, WHITE, PP_ALIGN.CENTER)
    txt(s, "DOMAIN-SPECIFIC RECOMMENDATIONS TO VALIDATE ON REAL DATA",
        0.99, 4.12, 11.5, 0.30, 10.5, True, TEAL)
    for i, (heading, line) in enumerate([
        ("RETAIL", "Confirm inventory demand and margins before reallocation"),
        ("EDUCATION", "Evaluate learning support using verified student records"),
        ("WEATHER", "Compare patterns with official long-term observations"),
        ("HEALTHCARE", "Validate service metrics before operational changes"),
        ("FINANCE", "Assess risk with verified market prices and trading costs")
    ]):
        y = 4.52 + i * 0.41
        txt(s, heading, 0.99, y, 2.08, 0.28, 9.6, True, TEAL)
        txt(s, line, 3.10, y, 9.32, 0.31, 11.0, False, TEXT)
    txt(s, "REPOSITORY", 0.96, 6.72, 1.4, 0.24, 9.5, True, SLATE)
    txt(s, GITHUB_URL, 2.43, 6.70, 10.1, 0.27, 10.2, False, CYAN)

    if len(prs.slides) != 12:
        raise RuntimeError(f"Expected 12 slides but generated {len(prs.slides)}")
    prs.save(str(OUTPUT_PPTX))
    with_summary = Presentation(str(OUTPUT_PPTX))
    if len(with_summary.slides) != 12:
        raise RuntimeError("Saved PowerPoint could not be reopened with 12 slides")

    # Source audit is based on actual existing files, not inferred source locations.
    audit = ["# Task 2 Presentation — Source Audit", "",
             "Generated from existing local simulated datasets and chart files.",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "", "## Project Sources", ""]
    for name in [p[0] for p in PROJECTS]:
        d = project_data[name]
        audit += [f"### {name}",
                  f"- Data: `{d['csv'].relative_to(ROOT).as_posix()}`",
                  f"- Chart: `{d['chart'].relative_to(ROOT).as_posix()}`",
                  f"- Notebook files: {len(d['notebooks'])}",
                  f"- PDF files: {len(d['pdfs'])}",
                  f"- PNG charts: {len(d['charts'])}", ""]
    audit += ["## Caveats", "",
              "- All project datasets are simulated.",
              "- Numerical metrics were computed from CSV files when this script ran.",
              "- Charts were embedded from existing project files; original images were not modified.",
              "- The presentation was verified structurally (12 slides), not visually in Microsoft PowerPoint.", ""]
    OUTPUT_SOURCES.write_text("\n".join(audit), encoding="utf-8")

    print("\nSUCCESS: 12-slide PowerPoint created")
    print("PowerPoint:", OUTPUT_PPTX)
    print("Source audit:", OUTPUT_SOURCES)
    print("Projects:", len(project_data))
    print("Original project files: unchanged")
    print("Open the .pptx in PowerPoint or Keynote and inspect all slides before submission.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nPRESENTATION BUILD FAILED: {exc}", file=sys.stderr)
        raise
