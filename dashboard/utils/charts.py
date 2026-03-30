import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dashboard.utils.formatters import truncate_label

# ---------------------------------------------------------------------------
# design constants dark theme, consistent palette
# ---------------------------------------------------------------------------

BACKGROUND_COLOR = "#0e1117"
PAPER_COLOR = "#0e1117"
PLOT_COLOR = "#161b22"
TEXT_COLOR = "#e6edf3"
GRID_COLOR = "#21262d"
ACCENT_COLOR = "#1f6feb"

COLOR_PALETTE = [
    "#1f6feb",
    "#388bfd",
    "#58a6ff",
    "#79c0ff",
    "#a5d6ff",
    "#cae8ff",
]

EXPENSE_CLASS_COLORS = {
    "Personnel Services": "#1f6feb",
    "Maintenance and Other Operating Expenses": "#388bfd",
    "Capital Outlay": "#58a6ff",
    "Financial Expenses": "#79c0ff",
}

BASE_LAYOUT = dict(
    paper_bgcolor=PAPER_COLOR,
    plot_bgcolor=PLOT_COLOR,
    font=dict(color=TEXT_COLOR, family="Inter, sans-serif", size=13),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
)


def horizontal_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str = "Amount (PHP)",
    color: str = ACCENT_COLOR,
) -> go.Figure:
    """
    Horizontal bar chart for ranked comparisons.
    Used for agency and department budget rankings.
    """
    df = df.copy()
    df[y_col] = df[y_col].apply(lambda v: truncate_label(str(v), 45))

    fig = go.Figure(
        go.Bar(
            x=df[x_col],
            y=df[y_col],
            orientation="h",
            marker=dict(color=color, opacity=0.9),
            hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text=title, font=dict(size=15, color=TEXT_COLOR)),
        xaxis_title=x_label,
        yaxis=dict(
            autorange="reversed",
            gridcolor=GRID_COLOR,
            zeroline=False,
        ),
        height=500,
    )

    return fig


def pie_chart(
    df: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str,
) -> go.Figure:
    """
    Donut chart for proportional breakdowns.
    Used for expense class distribution.
    """
    colors = [
        EXPENSE_CLASS_COLORS.get(name, ACCENT_COLOR)
        for name in df[names_col]
    ]

    fig = go.Figure(
        go.Pie(
            labels=df[names_col],
            values=df[values_col],
            hole=0.5,
            marker=dict(colors=colors),
            hovertemplate="%{label}<br>PHP %{value:,.0f}<br>%{percent}<extra></extra>",
            textinfo="percent+label",
            textfont=dict(size=12, color=TEXT_COLOR),
        )
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text=title, font=dict(size=15, color=TEXT_COLOR)),
        showlegend=False,
        height=420,
    )

    return fig


def treemap_chart(
    df: pd.DataFrame,
    values_col: str,
    names_col: str,
    parents_col: str,
    title: str,
) -> go.Figure:
    """
    Treemap for hierarchical budget distribution.
    Used for department breakdown.
    """
    fig = px.treemap(
        df,
        values=values_col,
        names=names_col,
        parents=parents_col,
        title=title,
        color=values_col,
        color_continuous_scale=[
            [0, "#161b22"],
            [0.5, "#1f6feb"],
            [1, "#cae8ff"],
        ],
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text=title, font=dict(size=15, color=TEXT_COLOR)),
        height=480,
        coloraxis_showscale=False,
    )

    fig.update_traces(
        textfont=dict(color=TEXT_COLOR),
        hovertemplate="%{label}<br>PHP %{value:,.0f}<extra></extra>",
    )

    return fig