"""
从 SQLite 读取文章数据并解析 annotation JSON 字段。
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "cache" / "monitor.db"


@st.cache_data(ttl=60)
def load_articles() -> pd.DataFrame:
    """加载所有已标注文章，解析 annotation 字段为平铺列。"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT id, url, title, summary, source_name, source_language,
               published_at, target_date, matched_keywords,
               relevance_score, annotation, created_at
        FROM articles
        WHERE annotation IS NOT NULL
        ORDER BY target_date DESC, relevance_score DESC
        """,
        conn,
    )
    conn.close()

    if df.empty:
        return df

    # 解析 annotation JSON
    def parse_ann(raw):
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    annotations = df["annotation"].apply(parse_ann)
    df["source_type"] = annotations.apply(lambda a: a.get("source_type", ""))
    df["stance"] = annotations.apply(lambda a: a.get("stance", ""))
    df["geographic_focus"] = annotations.apply(lambda a: a.get("geographic_focus", ""))
    df["summary_zh"] = annotations.apply(lambda a: a.get("summary_zh", ""))
    df["terminology_used"] = annotations.apply(lambda a: a.get("terminology_used", []))
    df["research_value"] = annotations.apply(lambda a: a.get("research_value", ""))

    # 解析 matched_keywords（JSON 数组字符串）
    def parse_kw(raw):
        try:
            return json.loads(raw) if raw else []
        except Exception:
            return []

    df["keywords_list"] = df["matched_keywords"].apply(parse_kw)

    # 日期列
    df["target_date"] = pd.to_datetime(df["target_date"]).dt.date
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce").fillna(0).astype(int)

    return df


def get_all_keywords(df: pd.DataFrame) -> list[str]:
    """返回所有出现过的关键词（去重排序）。"""
    kws = set()
    for lst in df["keywords_list"]:
        kws.update(lst)
    return sorted(kws)


def get_all_terminology(df: pd.DataFrame) -> pd.Series:
    """返回术语频率 Series（term → count）。"""
    terms = []
    for lst in df["terminology_used"]:
        terms.extend(lst)
    if not terms:
        return pd.Series(dtype=int)
    return pd.Series(terms).value_counts()
