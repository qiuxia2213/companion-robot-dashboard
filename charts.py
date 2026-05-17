"""
图表组件，基于 Plotly Express。
学术配色方案：#82B0D2 / #BEB8DC / #E7DAD2 / #FFB6C1 / #999999
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── 学术配色 ──────────────────────────────────────────────────────────────────
ACADEMIC_PALETTE = ["#82B0D2", "#BEB8DC", "#E7DAD2", "#FFB6C1", "#999999",
                    "#A8C8A0", "#F4C58E", "#C8A0C8"]

SOURCE_TYPE_COLORS = {
    "industry":   "#82B0D2",
    "mainstream": "#BEB8DC",
    "academic":   "#E7DAD2",
    "policy":     "#FFB6C1",
    "community":  "#999999",
}

STANCE_COLORS = {
    "promotional": "#FFB6C1",
    "neutral":     "#82B0D2",
    "critical":    "#BEB8DC",
    "ambiguous":   "#999999",
}

GEO_LABELS = {
    "china":  "中国",
    "us":     "美国",
    "japan":  "日本",
    "eu":     "欧盟",
    "global": "全球",
    "other":  "其他",
}

SOURCE_TYPE_LABELS = {
    "industry":   "产业",
    "mainstream": "主流媒体",
    "academic":   "学术",
    "policy":     "政策",
    "community":  "社区",
}

STANCE_LABELS = {
    "promotional": "宣传性",
    "neutral":     "中立",
    "critical":    "批判",
    "ambiguous":   "立场模糊",
}

# ── 通用布局基线 ───────────────────────────────────────────────────────────────
_BASE_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'Source Han Sans CN', 'Noto Sans SC', 'Inter', sans-serif",
              size=12, color="#2C3E50"),
    margin=dict(l=0, r=0, t=8, b=0),
    showlegend=False,
)

_GRID_COLOR = "#EBEBEB"


def daily_volume_chart(df: pd.DataFrame) -> go.Figure:
    """每日采集量柱状图（最近 30 天）。"""
    counts = df.groupby("target_date").size().reset_index(name="count")
    counts = counts.sort_values("target_date")

    fig = px.bar(
        counts,
        x="target_date",
        y="count",
        labels={"target_date": "日期", "count": "条目数"},
        color_discrete_sequence=["#82B0D2"],
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        xaxis_title="",
        yaxis_title="条目数",
        height=210,
    )
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridcolor=_GRID_COLOR, tickfont=dict(size=11))
    return fig


def source_type_pie(df: pd.DataFrame) -> go.Figure:
    """信源类型分布（圆环图）。"""
    if df.empty or df["source_type"].eq("").all():
        return _empty_figure("暂无信源数据")

    counts = df["source_type"].value_counts().reset_index()
    counts.columns = ["source_type", "count"]
    counts["label"] = counts["source_type"].map(SOURCE_TYPE_LABELS).fillna(counts["source_type"])

    fig = px.pie(
        counts,
        values="count",
        names="label",
        color="source_type",
        color_discrete_map={k: SOURCE_TYPE_COLORS.get(k, "#ccc") for k in counts["source_type"]},
        hole=0.45,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=11,
        marker=dict(line=dict(color="#FFFFFF", width=2)),
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        showlegend=False,
        height=210,
    )
    return fig


def keyword_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """关键词匹配频率（横向条形图，前 15）。"""
    from collections import Counter
    all_kw = []
    for lst in df["keywords_list"]:
        all_kw.extend(lst)

    if not all_kw:
        return _empty_figure("暂无关键词数据")

    counts = Counter(all_kw).most_common(top_n)
    kw_df = pd.DataFrame(counts, columns=["keyword", "count"]).sort_values("count")

    fig = px.bar(
        kw_df,
        x="count",
        y="keyword",
        orientation="h",
        labels={"count": "匹配次数", "keyword": "关键词"},
        color_discrete_sequence=["#82B0D2"],
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        height=max(210, len(counts) * 22),
        yaxis_title="",
        xaxis_title="匹配次数",
    )
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(showgrid=True, gridcolor=_GRID_COLOR, tickfont=dict(size=11))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
    return fig


def terminology_bar(term_series: pd.Series, top_n: int = 15) -> go.Figure:
    """文章术语频率（横向条形图，前 15）。"""
    if term_series.empty:
        return _empty_figure("暂无术语数据")

    top = term_series.head(top_n).reset_index()
    top.columns = ["term", "count"]
    top = top.sort_values("count")

    fig = px.bar(
        top,
        x="count",
        y="term",
        orientation="h",
        labels={"count": "出现次数", "term": "术语"},
        color_discrete_sequence=["#BEB8DC"],
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        height=max(210, len(top) * 22),
        yaxis_title="",
        xaxis_title="出现次数",
    )
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(showgrid=True, gridcolor=_GRID_COLOR, tickfont=dict(size=11))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
    return fig


def stance_geo_scatter(df: pd.DataFrame) -> go.Figure:
    """立场 × 地理 气泡图（气泡大小 = 相关度均值）。"""
    if df.empty:
        return _empty_figure("暂无数据")

    plot_df = df.copy()
    plot_df["geo_label"] = plot_df["geographic_focus"].map(GEO_LABELS).fillna(plot_df["geographic_focus"])
    plot_df["stance_label"] = plot_df["stance"].map(STANCE_LABELS).fillna(plot_df["stance"])

    agg = (
        plot_df.groupby(["geo_label", "stance_label", "stance"])
        .agg(count=("relevance_score", "size"), avg_score=("relevance_score", "mean"))
        .reset_index()
    )

    fig = px.scatter(
        agg,
        x="geo_label",
        y="stance_label",
        size="count",
        color="stance",
        color_discrete_map={k: STANCE_COLORS.get(k, "#ccc") for k in agg["stance"].unique()},
        hover_data={"count": True, "avg_score": ":.1f",
                    "geo_label": False, "stance_label": False, "stance": False},
        labels={"geo_label": "地理焦点", "stance_label": "立场",
                "count": "文章数", "avg_score": "平均相关度"},
        size_max=36,
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        height=250,
    )
    fig.update_xaxes(showgrid=True, gridcolor=_GRID_COLOR, tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridcolor=_GRID_COLOR, tickfont=dict(size=11))
    return fig


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=13, color="#aaa"),
    )
    fig.update_layout(
        height=180,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
