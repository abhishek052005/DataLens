



def build_universal_prompt(
    filename: str,
    row_count: int,
    col_count: int,
    numeric_stats: dict,      # {col_name: {mean, median, max, min, std, skew, outliers}}
    categorical_stats: dict,  # {col_name: {unique_count, top_5: {val: count}}}
    datetime_stats: dict,     # {col_name: {min_date, max_date, span_days, granularity}}
) -> str:

    # ── Build the data description block ──
    lines = []
    lines.append(f"DATASET: {filename}")
    lines.append(f"ROWS: {row_count:,} | COLUMNS: {col_count} (after cleanup)")
    lines.append("")

    if numeric_stats:
        lines.append("NUMERIC COLUMNS:")
        for col, s in numeric_stats.items():
            lines.append(
                f"- {col}: min={s['min']}, max={s['max']}, mean={s['mean']}, "
                f"median={s['median']}, std={s['std']}, skew={s['skew']}"
            )
        lines.append("")

    if categorical_stats:
        lines.append("CATEGORICAL COLUMNS:")
        for col, s in categorical_stats.items():
            top_vals = ", ".join(f"{k}({v})" for k, v in s["top_5"].items())
            lines.append(f"- {col}: {s['unique_count']} unique → [{top_vals}]")
        lines.append("")

    if datetime_stats:
        lines.append("DATETIME COLUMNS:")
        for col, s in datetime_stats.items():
            lines.append(
                f"- {col}: {s['min']} to {s['max']}, "
                # f"span={s['span_days']} days, granularity={s['granularity']}"
            )
        lines.append("")

    # ── Universal instructions (never change) ──
    lines.append("=" * 50)
    lines.append("INSTRUCTIONS:")
    lines.append("""You are a senior data analyst designing a professional dashboard from the stats above.

STEP 1 — ROLE ASSIGNMENT
Assign each column exactly one role:
- "measure"  → numeric column that is meaningful to sum/average
- "dimension" → categorical column with 2–50 unique values
- "time"     → datetime column
- "drop"     → ID, redundant, or too sparse to be useful

STEP 2 — COLUMN SELECTION
Select the best 6–10 columns that together answer DIFFERENT analytical questions:
- Must include at least 1 measure, 1 dimension, and 1 time column (if available)
- Drop columns that are redundant (two numerics with near-identical stats)
- Drop composite columns (name contains a separator joining two other column names)
- Prefer columns with lower null % and clearer semantic names
- If multiple dimensions exist, pick the ones with 3–15 unique values (best for charts)

STEP 3 — CHART ASSIGNMENT
For each selected column combination, assign ONE chart type:

| Combination                          | Chart Type      |
|--------------------------------------|-----------------|
| 1 measure (no grouping)              | Histogram       |
| 1 measure + 1 dimension (≤5 values)  | Pie / Donut     |
| 1 measure + 1 dimension (>5 values)  | Bar (sorted)    |
| 1 measure + 1 time                   | Line            |
| 1 measure + 1 time + 1 dimension     | Stacked Bar or Multi-series Line |
| 2 measures                           | Scatter         |
| 1 dimension + 2 measures             | Composed        |
| Single aggregated value              | KPI Card        |

Rules:
- Pie: only if ≤5 slices
- Bar: always sorted descending (unless natural order like months)
- Line: max 3 series
- Scatter: cap at 500 points
- Use only chart types supported by the Python dashboard: line, bar, pie, scatter, radar, area, histogram, stacked_bar, composed
- Do not use box plots
- Use line/area only for genuine time trends; use bars for categorical comparisons
- Use composed charts only when x is a dimension and y/y2 are distinct numeric measures
- Keep line charts to 3 series and stacked charts to 5; avoid long, overlapping category labels
- Give each chart a concise, specific title that describes the comparison
- Total charts: 4–6

STEP 4 — KPI CARDS
Pick 3–5 KPIs from measure columns:
- Use "sum" for counts/amounts, "mean" for rates/percentages, "count" for totals
- Format: "number", "currency", or "percent"

STEP 5 — INSIGHTS
Write 2–3 one-line insights based on the actual stats (not generic):
- Mention specific values (e.g., "peaked at X", "Y is 20% higher than Z")
- Flag anomalies (high skew, many outliers, one dominant category)

OUTPUT FORMAT (return ONLY valid JSON, no markdown):
{
  "selected_columns": [{"name": "", "role": "", "reason": ""}],
  "dropped_columns": [{"name": "", "reason": ""}],
  "kpis": [{"label": "", "column": "", "agg": "sum|mean|count", "format": "number|currency|percent"}],
  "charts": [{"title": "", "type": "line|bar|pie|scatter|radar|area|histogram|stacked_bar|composed", "x": "", "y": "", "y2": null, "group_by": null, "insight": ""}],
  "insights": [""]
}""")

    return "\n".join(lines)   