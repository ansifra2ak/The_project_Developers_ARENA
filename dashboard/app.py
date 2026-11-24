
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ==========================================================
# THE DEVELOPERS ARENA - TASK 2
# MULTI-DOMAIN INTERACTIVE ANALYTICS DASHBOARD
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent

st.set_page_config(
    page_title="Data Analysis Portfolio",
    page_icon="📊",
    layout="wide"
)

DATASETS = {
    "Supermarket Sales": (
        "data-analysis-portfolio",
        "supermarket_sales.csv"
    ),
    "Student Performance": (
        "student-performance-analysis",
        "students_cleaned.csv"
    ),
    "Weather Analysis": (
        "weather-data-analysis",
        "weather_cleaned.csv"
    ),
    "Healthcare Analysis": (
        "healthcare-data-analysis",
        "hospital_cleaned.csv"
    ),
    "Financial Market": (
        "financial-market-analysis",
        "market_cleaned.csv"
    )
}

# ----------------------------------------------------------
# COMMON FUNCTIONS
# ----------------------------------------------------------

def find_dataset(project):
    folder_name, filename = DATASETS[project]
    folder = ROOT / folder_name

    if not folder.exists():
        return None

    files = [
        p for p in folder.rglob(filename)
        if not any(
            part in {".venv", ".venv-1", ".git"}
            for part in p.parts
        )
    ]

    return sorted(files, key=lambda p: len(p.parts))[0] if files else None


@st.cache_data
def load_data(filename, modified_time):
    return pd.read_csv(filename)


def require_columns(data, columns):
    missing = set(columns) - set(data.columns)

    if missing:
        st.error("Missing columns: " + ", ".join(sorted(missing)))
        st.stop()


def filter_category(data, column, key):
    choices = sorted(data[column].dropna().unique().tolist())

    selected = st.sidebar.multiselect(
        f"Choose {column}",
        choices,
        default=choices,
        key=key
    )

    return data[data[column].isin(selected)].copy()


def filter_dates(data, key):
    data = data.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"])

    if data.empty:
        st.warning("No valid dates found.")
        st.stop()

    start = data["Date"].min().date()
    end = data["Date"].max().date()

    selected = st.sidebar.date_input(
        "Date range",
        value=(start, end),
        min_value=start,
        max_value=end,
        key=key
    )

    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        a, b = selected
        data = data[data["Date"].dt.date.between(a, b)]

    return data


def verify_rows(data):
    if data.empty:
        st.warning("No records match your selected filters.")
        st.stop()


def show_metrics(items):
    columns = st.columns(len(items))

    for col, (label, value) in zip(columns, items):
        col.metric(label, value)


def plot(fig):
    st.plotly_chart(fig, width="stretch")


def show_dataset(data, filename):
    st.divider()
    st.subheader("Dataset Preview")

    st.dataframe(
        data.head(100),
        width="stretch",
        hide_index=True
    )

    st.download_button(
        "Download Filtered Dataset",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv"
    )

    st.caption(f"Filtered records: {len(data):,}")


# ----------------------------------------------------------
# DASHBOARD NAVIGATION
# ----------------------------------------------------------

st.sidebar.title("📊 Data Analysis Portfolio")

project = st.sidebar.selectbox(
    "Select Project",
    list(DATASETS.keys())
)

st.sidebar.divider()
st.sidebar.caption("The Developers Arena | Task 2")

st.title("Multi-Domain Data Analysis Dashboard")
st.caption("Python • Pandas • Streamlit • Plotly")

st.info(
    "This dashboard uses simulated educational datasets "
    "from the five completed projects."
)

path = find_dataset(project)

if path is None:
    st.error(f"Dataset not found for {project}.")
    st.write("Expected filename:", DATASETS[project][1])
    st.stop()

df = load_data(str(path), path.stat().st_mtime)

st.subheader(project)

with st.expander("Dataset Information"):
    st.write("File:", str(path.relative_to(ROOT)))
    st.write("Rows:", len(df))
    st.write("Columns:", len(df.columns))
    st.write("Column names:", df.columns.tolist())


# ==========================================================
# PROJECT 1 - SUPERMARKET SALES
# ==========================================================

if project == "Supermarket Sales":

    require_columns(
        df,
        ["Date", "Category", "Product", "Sales", "Quantity"]
    )

    df = filter_dates(df, "sales_dates")
    df = filter_category(df, "Category", "sales_category")
    verify_rows(df)

    show_metrics([
        ("Total Revenue", f"₹{df['Sales'].sum():,.0f}"),
        ("Sales Records", f"{len(df):,}"),
        ("Units Sold", f"{df['Quantity'].sum():,.0f}"),
        ("Average Line Sale", f"₹{df['Sales'].mean():,.2f}")
    ])

    category = (
        df.groupby("Category", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
    )

    products = (
        df.groupby("Product", as_index=False)["Sales"]
        .sum()
        .nlargest(10, "Sales")
    )

    daily = (
        df.groupby("Date", as_index=False)["Sales"]
        .sum()
        .sort_values("Date")
    )

    left, right = st.columns(2)

    with left:
        plot(px.bar(
            category,
            x="Category",
            y="Sales",
            color="Category",
            title="Revenue by Category"
        ))

    with right:
        plot(px.bar(
            products,
            x="Product",
            y="Sales",
            color="Product",
            title="Top 10 Products"
        ))

    plot(px.line(
        daily,
        x="Date",
        y="Sales",
        title="Daily Sales Trend",
        markers=True
    ))

    show_dataset(df, "supermarket_filtered.csv")


# ==========================================================
# PROJECT 2 - STUDENT PERFORMANCE
# ==========================================================

elif project == "Student Performance":

    subjects = ["Mathematics", "Science", "English"]

    require_columns(
        df,
        ["Class", "Result", "AttendancePct",
         "AverageScore", *subjects]
    )

    df = filter_category(df, "Class", "student_class")
    df = filter_category(df, "Result", "student_result")
    verify_rows(df)

    pass_rate = df["Result"].eq("Pass").mean() * 100

    show_metrics([
        ("Students", f"{len(df):,}"),
        ("Pass Rate", f"{pass_rate:.1f}%"),
        ("Average Score", f"{df['AverageScore'].mean():.1f}"),
        ("Attendance", f"{df['AttendancePct'].mean():.1f}%")
    ])

    results = df["Result"].value_counts().reset_index()
    results.columns = ["Result", "Count"]

    averages = df[subjects].mean().reset_index()
    averages.columns = ["Subject", "AverageScore"]

    left, right = st.columns(2)

    with left:
        plot(px.pie(
            results,
            names="Result",
            values="Count",
            hole=0.4,
            title="Pass / Fail Distribution"
        ))

    with right:
        plot(px.bar(
            averages,
            x="Subject",
            y="AverageScore",
            color="Subject",
            title="Average Subject Scores"
        ))

    plot(px.scatter(
        df,
        x="AttendancePct",
        y="AverageScore",
        color="Result",
        opacity=0.55,
        title="Attendance vs Performance"
    ))

    show_dataset(df, "students_filtered.csv")


# ==========================================================
# PROJECT 3 - WEATHER ANALYSIS
# ==========================================================

elif project == "Weather Analysis":

    require_columns(
        df,
        ["Date", "City", "Season", "TemperatureC",
         "RainfallMM", "HumidityPct"]
    )

    df = filter_dates(df, "weather_dates")
    df = filter_category(df, "City", "weather_city")
    verify_rows(df)

    show_metrics([
        ("Observations", f"{len(df):,}"),
        ("Average Temp", f"{df['TemperatureC'].mean():.1f} °C"),
        ("Rainfall Total", f"{df['RainfallMM'].sum():,.0f} mm"),
        ("Average Humidity", f"{df['HumidityPct'].mean():.1f}%")
    ])

    monthly = df.copy()
    monthly["Month"] = (
        monthly["Date"].dt.to_period("M").dt.to_timestamp()
    )

    temp = (
        monthly.groupby(["Month", "City"], as_index=False)
        ["TemperatureC"].mean()
    )

    rainfall = (
        df.groupby(["Season", "City"], as_index=False)
        ["RainfallMM"].mean()
    )

    plot(px.line(
        temp,
        x="Month",
        y="TemperatureC",
        color="City",
        title="Monthly Temperature Trends",
        markers=True
    ))

    left, right = st.columns(2)

    with left:
        plot(px.bar(
            rainfall,
            x="Season",
            y="RainfallMM",
            color="City",
            barmode="group",
            title="Average Daily Rainfall by Season"
        ))

    with right:
        plot(px.scatter(
            df,
            x="TemperatureC",
            y="HumidityPct",
            color="City",
            opacity=0.5,
            title="Temperature vs Humidity"
        ))

    show_dataset(df, "weather_filtered.csv")


# ==========================================================
# PROJECT 4 - HEALTHCARE ANALYSIS
# ==========================================================

elif project == "Healthcare Analysis":

    require_columns(
        df,
        ["Date", "Department", "VisitID",
         "WaitMinutes", "LengthOfStayDays",
         "SatisfactionScore"]
    )

    df = filter_dates(df, "healthcare_dates")
    df = filter_category(
        df, "Department", "healthcare_department"
    )
    verify_rows(df)

    show_metrics([
        ("Visits", f"{len(df):,}"),
        ("Average Wait", f"{df['WaitMinutes'].mean():.1f} min"),
        ("Average Stay", f"{df['LengthOfStayDays'].mean():.1f} d"),
        ("Satisfaction", f"{df['SatisfactionScore'].mean():.2f}/5")
    ])

    department = (
        df.groupby("Department", as_index=False)
        .agg(
            Visits=("VisitID", "count"),
            AverageWait=("WaitMinutes", "mean")
        )
    )

    monthly = df.copy()
    monthly["Month"] = (
        monthly["Date"].dt.to_period("M").dt.to_timestamp()
    )

    monthly = (
        monthly.groupby("Month", as_index=False)
        .agg(Visits=("VisitID", "count"))
    )

    left, right = st.columns(2)

    with left:
        plot(px.bar(
            department,
            x="Department",
            y="AverageWait",
            color="Department",
            title="Waiting Times by Department"
        ))

    with right:
        plot(px.line(
            monthly,
            x="Month",
            y="Visits",
            title="Monthly Hospital Visits",
            markers=True
        ))

    plot(px.scatter(
        df,
        x="WaitMinutes",
        y="SatisfactionScore",
        color="Department",
        opacity=0.5,
        title="Waiting Time vs Satisfaction"
    ))

    show_dataset(df, "healthcare_filtered.csv")


# ==========================================================
# PROJECT 5 - FINANCIAL MARKET
# ==========================================================

elif project == "Financial Market":

    require_columns(
        df,
        ["Date", "Ticker", "Close", "Volume"]
    )

    df = filter_dates(df, "finance_dates")
    df = filter_category(df, "Ticker", "finance_ticker")
    verify_rows(df)

    df = df.sort_values(["Ticker", "Date"]).copy()

    df["NormalizedPrice"] = (
        df["Close"]
        / df.groupby("Ticker")["Close"].transform("first")
        * 100
    )

    df["DailyReturnPct"] = (
        df.groupby("Ticker")["Close"]
        .pct_change(fill_method=None) * 100
    )

    volatility = (
        df.groupby("Ticker")["DailyReturnPct"].std()
        * np.sqrt(252)
    )

    show_metrics([
        ("Stocks", f"{df['Ticker'].nunique()}"),
        ("Price Records", f"{len(df):,}"),
        ("Average Daily Return",
         f"{df['DailyReturnPct'].mean():.3f}%"),
        ("Mean Annualized Volatility",
         f"{volatility.mean():.2f}%")
    ])

    plot(px.line(
        df,
        x="Date",
        y="NormalizedPrice",
        color="Ticker",
        title="Normalized Stock Price Trends"
    ))

    left, right = st.columns(2)

    with left:
        vol = volatility.reset_index()
        vol.columns = ["Ticker", "VolatilityPct"]

        plot(px.bar(
            vol,
            x="Ticker",
            y="VolatilityPct",
            color="Ticker",
            title="Annualized Volatility"
        ))

    with right:
        returns = df.pivot_table(
            index="Date",
            columns="Ticker",
            values="DailyReturnPct"
        )

        correlation = returns.corr()

        if correlation.shape[0] >= 2:
            plot(px.imshow(
                correlation,
                zmin=-1,
                zmax=1,
                color_continuous_scale="RdBu_r",
                text_auto=".2f",
                title="Return Correlation"
            ))
        else:
            st.info("Select two or more stocks for correlation.")

    st.warning(
        "The financial dataset is fictional and "
        "does not constitute investment advice."
    )

    show_dataset(df, "financial_filtered.csv")


# ----------------------------------------------------------
# FOOTER
# ----------------------------------------------------------

st.divider()

st.caption(
    "The Developers Arena | Task 2 | "
    "Multi-Domain Analytics Portfolio"
)
