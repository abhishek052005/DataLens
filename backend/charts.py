import json

import pandas as pd
import plotly.graph_objects as go


def compute_chart_data(df: pd.DataFrame, plan: dict) -> dict:
    """Take an AI chart plan and compute the values used by the dashboard."""
    result = {"kpis": [], "charts": [], "insights": plan.get("insights", [])}

    for kpi in plan.get("kpis", []):
        column = kpi["column"]
        _require_columns(df, column)
        if kpi["agg"] == "sum":
            value = float(df[column].sum())
        elif kpi["agg"] == "mean":
            value = float(df[column].mean())
        else:
            value = int(df[column].count())
        result["kpis"].append({**kpi, "value": round(value, 2)})

    for chart in plan.get("charts", []):
        x = chart.get("x", "")
        y = chart.get("y", "")
        group = chart.get("group_by")
        chart_type = chart["type"]

        if chart_type == "histogram":
            column = x or y
            _require_columns(df, column)
            data = pd.to_numeric(df[column], errors="coerce").dropna()
        elif chart_type == "scatter":
            _require_columns(df, x, y)
            points = df[[x, y]].dropna()
            data = points.sample(min(500, len(points)), random_state=42)
        elif chart_type == "box":
            _require_columns(df, x, y)
            data = df[[x, y]].dropna()
        elif chart_type == "pie":
            _require_columns(df, x, y)
            data = df.groupby(x, observed=True)[y].sum().sort_values(ascending=False).head(5)
        elif chart_type in {"line", "area", "stacked_bar", "radar", "composed"}:
            _require_columns(df, x, y)
            if group:
                _require_columns(df, group)

            df_plot = df[[x, y] + ([group] if group else [])].copy()
            df_plot[x] = _monthly_dimension(df_plot[x])

            if group and chart_type in {"line", "stacked_bar"}:
                data = df_plot.groupby([x, group], observed=True)[y].sum().unstack(fill_value=0)
            elif chart_type == "stacked_bar":
                data = df_plot.groupby(x, observed=True)[y].sum().to_frame()
            elif chart_type == "composed" and chart.get("y2"):
                y2 = chart["y2"]
                _require_columns(df, y2)
                data = df.groupby(x, observed=True)[[y, y2]].sum()
            else:
                data = df_plot.groupby(x, observed=True)[y].sum()
                if chart_type == "composed":
                    data = data.sort_values(ascending=False)
        elif chart_type == "bar":
            _require_columns(df, x, y)
            data = df.groupby(x, observed=True)[y].sum().sort_values(ascending=False)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        result["charts"].append({**chart, "data": data})

    return result


def build_interactive_figures(dashboard_data: dict) -> dict:
    """Build Plotly figures that can be rendered directly in the web dashboard."""
    figures = []
    for chart in dashboard_data["charts"]:
        data = chart["data"]
        chart_type = chart["type"]
        x = chart.get("x", "")
        y = chart.get("y", "")
        figure = go.Figure()

        if chart_type in {"line", "area"}:
            if isinstance(data, pd.DataFrame):
                for column in data.columns[:3]:
                    figure.add_trace(go.Scatter(
                        x=data.index.astype(str).tolist(),
                        y=data[column].tolist(),
                        name=str(column),
                        mode="lines+markers",
                        fill="tozeroy" if chart_type == "area" and len(figure.data) == 0 else None,
                    ))
            else:
                figure.add_trace(go.Scatter(
                    x=data.index.astype(str).tolist(),
                    y=data.tolist(),
                    name=y,
                    mode="lines+markers",
                    fill="tozeroy" if chart_type == "area" else None,
                ))
        elif chart_type in {"bar", "composed"}:
            if isinstance(data, pd.DataFrame) and chart_type == "composed" and chart.get("y2"):
                categories = data.index.astype(str).tolist()
                figure.add_trace(go.Bar(x=categories, y=data[y].tolist(), name=y))
                figure.add_trace(go.Scatter(
                    x=categories, y=data[chart["y2"]].tolist(),
                    name=chart["y2"], mode="lines+markers", yaxis="y2",
                ))
                figure.update_layout(
                    yaxis2={"overlaying": "y", "side": "right", "showgrid": False},
                )
            elif isinstance(data, pd.DataFrame):
                for column in data.columns[:5]:
                    figure.add_trace(go.Bar(
                        x=data.index.astype(str).tolist(),
                        y=data[column].tolist(),
                        name=str(column),
                    ))
            else:
                values = data.nlargest(12) if len(data) > 12 else data
                figure.add_trace(go.Bar(
                    x=values.index.astype(str).tolist(),
                    y=values.tolist(),
                    name=y,
                    marker={"color": "#818cf8"},
                ))
        elif chart_type == "stacked_bar":
            if isinstance(data, pd.DataFrame):
                for column in data.columns[:5]:
                    figure.add_trace(go.Bar(
                        x=data.index.astype(str).tolist(),
                        y=data[column].tolist(),
                        name=str(column),
                    ))
            else:
                figure.add_trace(go.Bar(
                    x=data.index.astype(str).tolist(), y=data.tolist(), name=y,
                ))
            figure.update_layout(barmode="stack")
        elif chart_type == "pie":
            figure.add_trace(go.Pie(
                labels=data.index.astype(str).tolist(),
                values=data.tolist(),
                hole=0.58,
                textinfo="label+percent",
                marker={"colors": ["#818cf8", "#34d399", "#38bdf8", "#fbbf24", "#fb7185"]},
            ))
        elif chart_type == "scatter":
            figure.add_trace(go.Scatter(
                x=data[x].tolist(), y=data[y].tolist(),
                mode="markers", name=y,
                marker={"color": "#a78bfa", "size": 8, "opacity": 0.8},
            ))
        elif chart_type == "histogram":
            values = pd.to_numeric(data, errors="coerce").dropna()
            figure.add_trace(go.Histogram(
                x=values.tolist(), name=x or y,
                marker={"color": "#818cf8"},
            ))
        elif chart_type == "radar":
            categories = data.index.astype(str).tolist()[:12]
            values = data.tolist()[:12]
            figure.add_trace(go.Scatterpolar(
                r=values + values[:1],
                theta=categories + categories[:1],
                fill="toself",
                name=y,
                line={"color": "#a3e635"},
                fillcolor="rgba(163, 230, 53, 0.2)",
            ))
        elif chart_type == "box":
            for category in data[x].drop_duplicates().astype(str).head(12):
                values = data.loc[data[x].astype(str) == category, y].dropna()
                figure.add_trace(go.Box(
                    y=values.tolist(), name=category, boxpoints="outliers",
                ))

        figure.update_layout(
            title={"text": chart.get("title", ""), "x": 0.02, "xanchor": "left"},
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, sans-serif", "color": "#cbd5e1", "size": 12},
            margin={"l": 48, "r": 30, "t": 58, "b": 55},
            height=340,
            hovermode="x unified" if chart_type in {"line", "area"} else "closest",
            legend={"orientation": "h", "y": -0.22, "x": 0},
            xaxis={"gridcolor": "rgba(148,163,184,0.12)", "automargin": True},
            yaxis={"gridcolor": "rgba(148,163,184,0.12)", "automargin": True},
            bargap=0.28,
            showlegend=chart_type in {"line", "area", "stacked_bar", "composed", "box"},
        )
        if chart.get("insight"):
            figure.add_annotation(
                text=str(chart["insight"]),
                xref="paper", yref="paper", x=0, y=1.12,
                showarrow=False, font={"color": "#94a3b8", "size": 11},
            )
        figures.append({
            "title": chart.get("title", ""),
            "type": chart_type,
            "figure": json.loads(figure.to_json()),
        })

    return {
        "kpis": dashboard_data["kpis"],
        "charts": figures,
        "insights": dashboard_data.get("insights", []),
        "row_count": dashboard_data.get("row_count", 0),
    }


def _require_columns(df: pd.DataFrame, *columns: str | None) -> None:
    missing = [
        column for column in columns
        if not isinstance(column, str) or column not in df.columns
    ]
    if missing:
        labels = ", ".join(
            "<missing>" if column is None else repr(column)
            for column in missing
        )
        raise ValueError(f"Chart column(s) not found or invalid: {labels}")


def _monthly_dimension(values: pd.Series) -> pd.Series:
    if not (
        pd.api.types.is_datetime64_any_dtype(values)
        or pd.api.types.is_object_dtype(values)
        or pd.api.types.is_string_dtype(values)
    ):
        return values

    parsed = pd.to_datetime(values, errors="coerce", format="mixed")
    valid = parsed.notna()
    if valid.sum() < max(2, int(len(values) * 0.8)):
        return values

    monthly = values.astype(str).astype(object)
    monthly.loc[valid] = parsed.loc[valid].dt.strftime("%Y-%m")
    return monthly
