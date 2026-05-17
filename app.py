"""
伴侣机器人监测仪表盘
启动：cd /path/to/companion-robot-monitor && streamlit run visualizations/app.py
"""
import datetime

import pandas as pd
import streamlit as st

from charts import (
    daily_volume_chart,
    keyword_bar,
    source_type_pie,
    stance_geo_scatter,
    terminology_bar,
    STANCE_LABELS,
    GEO_LABELS,
)
from data_loader import get_all_keywords, get_all_terminology, load_articles

# ── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="伴侣机器人监测仪表盘",
    page_icon="robot",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全局样式 ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Source Han Sans CN', 'Noto Sans SC', 'Inter', sans-serif;
    }

    /* KPI 卡片 */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        padding: 18px 16px 14px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 600;
        color: #2C3E50;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #7F8C8D;
        margin-top: 5px;
        letter-spacing: 0.02em;
    }

    /* 图表区容器 */
    .chart-card {
        background: #FFFFFF;
        border: 1px solid #E8ECF0;
        border-radius: 8px;
        padding: 16px 16px 8px;
        margin-bottom: 16px;
    }

    /* 区块标题 */
    .section-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #5D6D7E;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 10px;
        padding-bottom: 6px;
        border-bottom: 1.5px solid #82B0D2;
    }

    /* 页面大标题修正 */
    h1 { font-size: 1.5rem !important; font-weight: 600 !important; }

    /* 数据表格 */
    table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
    th { background: #F5F7FA; color: #5D6D7E; font-weight: 600;
         padding: 8px 10px; text-align: left; border-bottom: 2px solid #E8ECF0; }
    td { padding: 7px 10px; border-bottom: 1px solid #F0F3F6; color: #2C3E50; }
    tr:hover td { background: #FAFBFC; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── 数据加载 ──────────────────────────────────────────────────────────────────
df_all = load_articles()

if df_all.empty:
    st.warning("数据库中暂无已标注文章。等待每日自动抓取后刷新。")
    st.stop()


# ── 侧边栏 ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 过滤器")
    search_query = st.text_input("搜索标题 / 摘要", placeholder="输入关键字...")

    all_kws = get_all_keywords(df_all)
    selected_kws = st.multiselect("关键词筛选", all_kws)

    st.markdown("---")
    date_min = df_all["target_date"].min()
    date_max = df_all["target_date"].max()
    st.markdown(
        f"**共 {len(df_all)} 条记录**  \n"
        f"{date_min} ~ {date_max}"
    )
    if st.button("刷新数据"):
        st.cache_data.clear()
        st.rerun()


# ── 过滤 ──────────────────────────────────────────────────────────────────────
df = df_all.copy()
if search_query:
    mask = (
        df["title"].str.contains(search_query, case=False, na=False)
        | df["summary"].str.contains(search_query, case=False, na=False)
        | df["summary_zh"].str.contains(search_query, case=False, na=False)
    )
    df = df[mask]

if selected_kws:
    df = df[df["keywords_list"].apply(lambda lst: any(k in lst for k in selected_kws))]


# ── 顶部：标题 + KPI ──────────────────────────────────────────────────────────
st.markdown("# 伴侣机器人监测仪表盘")
latest_time = df_all["created_at"].max()
ts = latest_time.strftime("%Y-%m-%d %H:%M") if pd.notna(latest_time) else "未知"
st.caption(f"伴侣机器人议题动态追踪系统 · 数据更新于 {ts}")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
weekly_new = int((df_all["target_date"] >= one_week_ago).sum())
avg_score = df_all["relevance_score"].mean()
n_china = int((df_all["geographic_focus"] == "china").sum())

for col, value, label in [
    (col1, len(df_all), "总条目数"),
    (col2, weekly_new, "本周新增"),
    (col3, f"{avg_score:.1f}", "平均相关度"),
    (col4, n_china, "中国焦点"),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

if len(df_all) < 5:
    st.info(f"数据积累中（当前 {len(df_all)} 条），图表待数据增多后更丰富。")


# ── 图表区 ────────────────────────────────────────────────────────────────────
left, right = st.columns([1.1, 1])

with left:
    st.markdown('<div class="chart-card">'
                '<div class="section-title">每日采集量（最近 30 天）</div>', unsafe_allow_html=True)
    st.plotly_chart(daily_volume_chart(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">'
                '<div class="section-title">信源类型分布</div>', unsafe_allow_html=True)
    st.plotly_chart(source_type_pie(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">'
                '<div class="section-title">立场与地理焦点分布</div>', unsafe_allow_html=True)
    st.plotly_chart(stance_geo_scatter(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="chart-card">'
                '<div class="section-title">关键词匹配频率（前 15）</div>', unsafe_allow_html=True)
    st.plotly_chart(keyword_bar(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">'
                '<div class="section-title">文章术语频率（前 15）</div>', unsafe_allow_html=True)
    term_series = get_all_terminology(df)
    st.plotly_chart(terminology_bar(term_series), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── 文章明细表 ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 文章明细")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 1])

with filter_col1:
    date_range = st.date_input(
        "日期范围",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

with filter_col2:
    stance_options = sorted(df_all["stance"].dropna().unique().tolist())
    stance_labels = [STANCE_LABELS.get(s, s) for s in stance_options]
    selected_stances_labels = st.multiselect("立场", stance_labels)
    selected_stances = [
        s for s, l in zip(stance_options, stance_labels) if l in selected_stances_labels
    ]

with filter_col3:
    geo_options = sorted(df_all["geographic_focus"].dropna().unique().tolist())
    geo_labels = [GEO_LABELS.get(g, g) for g in geo_options]
    selected_geo_labels = st.multiselect("地理焦点", geo_labels)
    selected_geo = [
        g for g, l in zip(geo_options, geo_labels) if l in selected_geo_labels
    ]

with filter_col4:
    score_range = st.slider("相关度", min_value=0, max_value=10, value=(0, 10))

# 应用表格过滤
tbl = df.copy()

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    tbl = tbl[
        (tbl["target_date"] >= date_range[0]) & (tbl["target_date"] <= date_range[1])
    ]

if selected_stances:
    tbl = tbl[tbl["stance"].isin(selected_stances)]

if selected_geo:
    tbl = tbl[tbl["geographic_focus"].isin(selected_geo)]

tbl = tbl[
    (tbl["relevance_score"] >= score_range[0]) & (tbl["relevance_score"] <= score_range[1])
]

tbl = tbl.sort_values("relevance_score", ascending=False)

st.caption(f"筛选结果：{len(tbl)} 条")

if tbl.empty:
    st.info("没有符合条件的文章。")
else:
    display = tbl[["title", "url", "source_name", "source_type", "stance",
                   "geographic_focus", "relevance_score", "target_date"]].copy()

    display["信源类型"] = display["source_type"].map(
        {"industry": "产业", "mainstream": "主流媒体", "academic": "学术",
         "policy": "政策", "community": "社区"}
    ).fillna(display["source_type"])

    display["立场"] = display["stance"].map(
        {"promotional": "宣传性", "neutral": "中立", "critical": "批判", "ambiguous": "模糊"}
    ).fillna(display["stance"])

    display["地理"] = display["geographic_focus"].map(GEO_LABELS).fillna(display["geographic_focus"])

    display["标题"] = display.apply(
        lambda r: f'<a href="{r["url"]}" target="_blank">{r["title"][:60]}{"…" if len(r["title"]) > 60 else ""}</a>',
        axis=1,
    )

    display = display.rename(columns={
        "source_name": "来源",
        "relevance_score": "相关度",
        "target_date": "抓取日期",
    })

    st.markdown(
        display[["标题", "来源", "信源类型", "立场", "地理", "相关度", "抓取日期"]]
        .to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

    with st.expander("查看摘要（中文）"):
        for _, row in tbl.head(10).iterrows():
            st.markdown(f"**[{row['title'][:70]}]({row['url']})**")
            st.markdown(f"*相关度 {row['relevance_score']}/10 · {row['source_name']} · {row['target_date']}*")
            if row["summary_zh"]:
                st.markdown(row["summary_zh"])
            else:
                st.markdown(row["summary"][:200] + "…" if row["summary"] else "（无摘要）")
            st.markdown("---")
