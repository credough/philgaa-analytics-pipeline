import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dashboard.utils.formatters import truncate_label

# ---------------------------------------------------------------------------
# Design constants
# ---------------------------------------------------------------------------

BACKGROUND_COLOR  = "#0e1117"
PAPER_COLOR       = "#0e1117"
PLOT_COLOR        = "#161b22"
TEXT_COLOR        = "#e6edf3"
GRID_COLOR        = "#21262d"
MUTED_TEXT        = "#8b949e"

# Primary palette — blue, teal, amber, red, purple, slate
PALETTE = [
    "#58a6ff",   # blue
    "#2ea88a",   # teal
    "#f0b429",   # amber
    "#f85149",   # red
    "#bc8cff",   # purple
    "#79c0ff",   # light blue
    "#56d364",   # green
    "#ffa657",   # orange
]

# Expense class semantic colors — intentional, not decorative
EXPENSE_CLASS_COLORS = {
    "Personnel Services":                         "#58a6ff",
    "Maintenance and Other Operating Expenses":   "#2ea88a",
    "Capital Outlay":                             "#f0b429",
    "Financial Expenses":                         "#f85149",
}

# Department tier colors — top departments get warmer colors
DEPARTMENT_COLOR_SCALE = [
    [0.0,  "#1a1f2e"],
    [0.3,  "#1a3a5c"],
    [0.6,  "#1a6060"],
    [0.85, "#1a7f64"],
    [1.0,  "#f0b429"],
]


def _base_layout(title: str, height: int = 500) -> dict:
    """Returns a consistent base layout dict for all charts."""
    return dict(
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
        font=dict(
            color=TEXT_COLOR,
            family="Inter, -apple-system, sans-serif",
            size=12,
        ),
        margin=dict(l=20, r=20, t=55, b=40),
        title=dict(
            text=title,
            font=dict(size=14, color=TEXT_COLOR, family="Inter, sans-serif"),
            x=0,
            xanchor="left",
            pad=dict(b=12),
        ),
        height=height,
    )


def horizontal_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str = "Amount (PHP)",
    use_palette: bool = True,
) -> go.Figure:
    """
    Horizontal bar chart for ranked comparisons.
    Each bar gets a distinct color from the palette when use_palette=True.
    """
    df = df.copy()
    df[y_col] = df[y_col].apply(lambda v: truncate_label(str(v), 45))

    n = len(df)
    colors = [PALETTE[i % len(PALETTE)] for i in range(n)]

    fig = go.Figure(
        go.Bar(
            x=df[x_col],
            y=df[y_col],
            orientation="h",
            marker=dict(
                color=colors if use_palette else PALETTE[0],
                line=dict(width=0),
            ),
            hovertemplate="%{y}<br><b>PHP %{x:,.0f}</b><extra></extra>",
        )
    )

    layout = _base_layout(title, height=max(420, n * 36 + 100))
    layout.update(
        xaxis=dict(
            title=dict(text=x_label, font=dict(size=11, color=MUTED_TEXT)),
            gridcolor=GRID_COLOR,
            zeroline=False,
            tickfont=dict(size=10, color=MUTED_TEXT),
            tickformat="$.3s",
        ),
        yaxis=dict(
            autorange="reversed",
            gridcolor=GRID_COLOR,
            zeroline=False,
            tickfont=dict(size=11, color=TEXT_COLOR),
        ),
        bargap=0.28,
    )
    fig.update_layout(**layout)
    return fig


def pie_chart(
    df: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str,
) -> go.Figure:
    """
    Donut chart for proportional breakdowns.
    Uses semantic expense class colors when names match — otherwise palette.
    """
    colors = [
        EXPENSE_CLASS_COLORS.get(name, PALETTE[i % len(PALETTE)])
        for i, name in enumerate(df[names_col])
    ]

    label_map = {
        "Maintenance and Other Operating Expenses": "MOOE",
        "Personnel Services":                       "PS",
        "Capital Outlay":                           "CO",
        "Financial Expenses":                       "FE",
    }
    display_labels = [label_map.get(n, n) for n in df[names_col]]

    fig = go.Figure(
        go.Pie(
            labels=display_labels,
            customdata=df[names_col],
            values=df[values_col],
            hole=0.55,
            marker=dict(
                colors=colors,
                line=dict(color=BACKGROUND_COLOR, width=3),
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "PHP %{value:,.0f}<br>"
                "%{percent}<extra></extra>"
            ),
            textinfo="label+percent",
            textfont=dict(size=13, color=TEXT_COLOR),
        )
    )

    layout = _base_layout(title, height=440)
    layout.update(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=MUTED_TEXT),
        ),
    )
    fig.update_layout(**layout)
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
    Blue-to-amber gradient encodes relative budget size.
    """
    fig = px.treemap(
        df,
        values=values_col,
        names=names_col,
        parents=parents_col,
        title=title,
        color=values_col,
        color_continuous_scale=DEPARTMENT_COLOR_SCALE,
    )

    layout = _base_layout(title, height=500)
    layout.update(coloraxis_showscale=False)
    fig.update_layout(**layout)

    fig.update_traces(
        textfont=dict(color=TEXT_COLOR, size=12),
        hovertemplate="%{label}<br><b>PHP %{value:,.0f}</b><extra></extra>",
        marker=dict(line=dict(color=BACKGROUND_COLOR, width=2)),
    )

    return fig