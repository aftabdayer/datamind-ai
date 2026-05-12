import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from groq import Groq
import json
import io
import os
from datetime import datetime
from report_generator import generate_pdf_report
from data_analyzer import analyze_dataframe, detect_anomalies, get_column_insights

st.set_page_config(
    page_title="DataMind AI — Business Report Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.hero {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    border-radius: 20px; padding: 3rem 2.5rem 2.5rem;
    text-align: center; margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.08);
}
.hero-badge {
    display: inline-block; background: rgba(102,126,234,0.2);
    border: 1px solid rgba(102,126,234,0.4); color: #a5b4fc;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 2px;
    text-transform: uppercase; padding: 0.3rem 1rem;
    border-radius: 999px; margin-bottom: 1rem;
}
.hero h1 { color: white; font-size: 2.6rem; font-weight: 800; margin: 0 0 0.5rem; letter-spacing: -1px; }
.hero h1 span { color: #818cf8; }
.hero p { color: rgba(255,255,255,0.6); font-size: 1rem; margin: 0; }
.hero-pills { display: flex; justify-content: center; gap: 0.75rem; margin-top: 1.5rem; flex-wrap: wrap; }
.hero-pill {
    background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.7); font-size: 0.78rem; font-weight: 500;
    padding: 0.35rem 0.9rem; border-radius: 999px;
}
.metric-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.metric-card {
    background: white; border: 1px solid #f0f0f0; border-radius: 16px;
    padding: 1.25rem 1rem; text-align: center; position: relative; overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #667eea, #764ba2);
}
.metric-num { font-size: 2rem; font-weight: 800; color: #1a202c; line-height: 1; }
.metric-label { font-size: 0.72rem; color: #9ca3af; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 0.4rem; }
.metric-icon { font-size: 1.4rem; margin-bottom: 0.3rem; }
.health-box { border-radius: 16px; padding: 1.5rem 2rem; margin-bottom: 1.5rem; border: 1px solid; display: flex; align-items: center; gap: 1.5rem; }
.health-excellent { background: #f0fdf4; border-color: #86efac; }
.health-good { background: #eff6ff; border-color: #93c5fd; }
.health-fair { background: #fffbeb; border-color: #fcd34d; }
.health-poor { background: #fef2f2; border-color: #fca5a5; }
.health-score-circle { width: 72px; height: 72px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.6rem; font-weight: 800; }
.health-excellent .health-score-circle { background: #dcfce7; color: #16a34a; }
.health-good .health-score-circle { background: #dbeafe; color: #1d4ed8; }
.health-fair .health-score-circle { background: #fef9c3; color: #a16207; }
.health-poor .health-score-circle { background: #fee2e2; color: #dc2626; }
.health-text h3 { margin: 0 0 0.25rem; font-size: 1rem; font-weight: 700; color: #1a202c; }
.health-text p { margin: 0; font-size: 0.88rem; color: #6b7280; line-height: 1.5; }
.section-hdr { display: flex; align-items: center; gap: 0.6rem; margin: 2rem 0 1rem; }
.section-hdr-icon { width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; font-size: 0.9rem; flex-shrink: 0; }
.section-hdr h2 { margin: 0; font-size: 1.15rem; font-weight: 700; color: #1a202c; }
.section-hdr span { font-size: 0.8rem; color: #9ca3af; margin-left: 0.5rem; font-weight: 400; }
.card { background: white; border: 1px solid #f0f0f0; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem; line-height: 1.75; color: #374151; font-size: 0.95rem; }
.card-finding { border-left: 4px solid #667eea; background: linear-gradient(to right, #f8f9ff, white); }
.card-anomaly { border-left: 4px solid #f59e0b; background: linear-gradient(to right, #fffbeb, white); }
.card-reco { border-left: 4px solid #10b981; background: linear-gradient(to right, #f0fdf4, white); }
.finding-num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 0.72rem; font-weight: 700; border-radius: 50%; margin-right: 0.5rem; vertical-align: middle; }
.reco-num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: linear-gradient(135deg, #10b981, #059669); color: white; font-size: 0.72rem; font-weight: 700; border-radius: 50%; margin-right: 0.5rem; vertical-align: middle; }
.badge { display: inline-block; font-size: 0.7rem; font-weight: 700; padding: 0.18rem 0.6rem; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.5px; margin-left: 0.5rem; vertical-align: middle; }
.badge-high { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
.badge-medium { background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; }
.badge-low { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }
.chat-container { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 16px; padding: 1.25rem; margin-bottom: 1rem; max-height: 480px; overflow-y: auto; }
.chat-msg-user { display: flex; justify-content: flex-end; margin-bottom: 0.75rem; }
.chat-msg-user .bubble { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 0.75rem 1.1rem; border-radius: 16px 16px 4px 16px; max-width: 75%; font-size: 0.9rem; line-height: 1.5; }
.chat-msg-ai { display: flex; gap: 0.6rem; margin-bottom: 0.75rem; }
.chat-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0; color: white; font-weight: 700; }
.chat-msg-ai .bubble { background: white; border: 1px solid #e5e7eb; color: #374151; padding: 0.75rem 1.1rem; border-radius: 4px 16px 16px 16px; max-width: 80%; font-size: 0.9rem; line-height: 1.6; }
.forecast-badge { display: inline-block; background: rgba(102,126,234,0.1); border: 1px solid rgba(102,126,234,0.3); color: #667eea; font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.7rem; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.5px; margin-left: 0.5rem; }
.stButton > button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 0.85rem 2rem; font-weight: 700; font-size: 1rem; width: 100%; transition: all 0.2s; box-shadow: 0 4px 20px rgba(102,126,234,0.4); }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 25px rgba(102,126,234,0.5); }
.download-btn > button { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; box-shadow: 0 4px 20px rgba(16,185,129,0.4) !important; }
.stAlert { border-radius: 12px; }
div[data-testid="stExpander"] { border: 1px solid #f0f0f0; border-radius: 12px; margin-bottom: 0.5rem; }
.footer { text-align: center; color: #d1d5db; font-size: 0.78rem; margin-top: 3rem; padding: 1.5rem; border-top: 1px solid #f3f4f6; }
.footer strong { color: #9ca3af; }
</style>
""", unsafe_allow_html=True)


def init_groq(api_key):
    return Groq(api_key=api_key)


def call_groq(client, prompt, system="", max_tokens=1800):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def load_data(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, encoding=enc)
            except Exception:
                continue
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file format.")


def compute_health_score(df, anomalies):
    score = 100
    missing_pct = df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100
    score -= min(30, missing_pct * 3)
    dupes = anomalies.get("duplicate_rows", {}).get("pct", 0)
    score -= min(20, dupes * 2)
    outlier_cols = len(anomalies.get("outliers", {}))
    score -= min(20, outlier_cols * 5)
    constant_cols = len(anomalies.get("constant_columns", []))
    score -= min(10, constant_cols * 5)
    score = max(0, round(score))
    if score >= 85:
        return score, "Excellent", "health-excellent"
    elif score >= 65:
        return score, "Good", "health-good"
    elif score >= 45:
        return score, "Fair", "health-fair"
    else:
        return score, "Poor", "health-poor"


def build_charts(df):
    charts = []
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "year", "month", "day"])]
    PURPLE = "#667eea"
    COLORS = [PURPLE, "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a"]
    base = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,249,255,0.6)",
                font=dict(family="Inter", size=11, color="#374151"),
                margin=dict(t=45, b=30, l=30, r=20), height=320)

    if date_cols and numeric_cols:
        for dc in date_cols:
            nc = numeric_cols[0]
            try:
                tmp = df[[dc, nc]].dropna().copy()
                tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
                tmp = tmp.dropna().sort_values(dc)
                if len(tmp) > 2:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=tmp[dc], y=tmp[nc], mode="lines",
                        line=dict(color=PURPLE, width=2.5), fill="tozeroy",
                        fillcolor="rgba(102,126,234,0.1)", name=nc))
                    fig.update_layout(**base, title=dict(text=f"📈 {nc} Trend Over Time", font=dict(size=13, color="#1a202c")))
                    fig.update_xaxes(showgrid=False, linecolor="#e5e7eb")
                    fig.update_yaxes(gridcolor="#f0f0f0", linecolor="#e5e7eb")
                    charts.append(fig)
                    break
            except Exception:
                pass

    if cat_cols and numeric_cols:
        best_cat = next((c for c in cat_cols if 2 <= df[c].nunique() <= 15), None)
        if best_cat:
            nc = numeric_cols[0]
            agg = df.groupby(best_cat)[nc].mean().sort_values(ascending=False).head(12)
            fig = go.Figure(go.Bar(
                x=agg.index.astype(str), y=agg.values,
                marker=dict(color=agg.values, colorscale=[[0,"#f0f4ff"],[1,PURPLE]], line=dict(width=0))))
            fig.update_layout(**base, title=dict(text=f"📊 Avg {nc} by {best_cat}", font=dict(size=13, color="#1a202c")))
            fig.update_xaxes(showgrid=False, linecolor="#e5e7eb")
            fig.update_yaxes(gridcolor="#f0f0f0", linecolor="#e5e7eb")
            charts.append(fig)

    if len(numeric_cols) >= 3:
        corr = df[numeric_cols[:8]].corr().round(2)
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            colorscale=[[0,"#f093fb"],[0.5,"#ffffff"],[1,PURPLE]],
            zmid=0, text=corr.values.round(2), texttemplate="%{text}", textfont={"size": 9}))
        fig.update_layout(**base, title=dict(text="🔗 Correlation Heatmap", font=dict(size=13, color="#1a202c")), height=340)
        charts.append(fig)

    if numeric_cols:
        target = numeric_cols[0]
        data = df[target].dropna()
        if len(data) > 5:
            fig = go.Figure()
            fig.add_trace(go.Violin(y=data, name=target, box_visible=True, meanline_visible=True,
                fillcolor="rgba(102,126,234,0.25)", line_color=PURPLE))
            fig.update_layout(**base, title=dict(text=f"🎻 {target} Distribution", font=dict(size=13, color="#1a202c")))
            fig.update_yaxes(gridcolor="#f0f0f0")
            charts.append(fig)

    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        color_col = next((c for c in cat_cols if df[c].nunique() <= 8), None)
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
            trendline="ols" if not color_col else None,
            color_discrete_sequence=COLORS, opacity=0.75)
        fig.update_traces(marker=dict(size=9, line=dict(width=1, color="white")))
        fig.update_layout(**base, title=dict(text=f"🔵 {x_col} vs {y_col}", font=dict(size=13, color="#1a202c")))
        fig.update_xaxes(showgrid=False, linecolor="#e5e7eb")
        fig.update_yaxes(gridcolor="#f0f0f0", linecolor="#e5e7eb")
        charts.append(fig)

    if cat_cols and numeric_cols:
        for c in cat_cols:
            if 2 <= df[c].nunique() <= 8:
                nc = numeric_cols[0]
                agg = df.groupby(c)[nc].sum().sort_values(ascending=False)
                fig = go.Figure(go.Pie(
                    values=agg.values, labels=agg.index.astype(str), hole=0.45,
                    marker=dict(colors=COLORS), textfont=dict(size=11)))
                fig.update_layout(**base, title=dict(text=f"🥧 {nc} Share by {c}", font=dict(size=13, color="#1a202c")),
                    showlegend=True, legend=dict(font=dict(size=10)))
                charts.append(fig)
                break

    return charts[:6]


def build_forecast_chart(df):
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date","time","year","month"])]
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not date_cols or not numeric_cols:
        return None
    dc, nc = date_cols[0], numeric_cols[0]
    try:
        tmp = df[[dc, nc]].dropna().copy()
        tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
        tmp = tmp.dropna().sort_values(dc)
        if len(tmp) < 4:
            return None
        tmp["x_num"] = (tmp[dc] - tmp[dc].min()).dt.days
        coeffs = np.polyfit(tmp["x_num"], tmp[nc], 1)
        last_x = tmp["x_num"].max()
        future_x = np.linspace(last_x, last_x * 1.3, 8)
        future_dates = tmp[dc].min() + pd.to_timedelta(future_x, unit="D")
        future_vals = np.polyval(coeffs, future_x)
        trend_vals = np.polyval(coeffs, tmp["x_num"])
        PURPLE = "#667eea"
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tmp[dc], y=tmp[nc], mode="markers+lines", name="Actual",
            line=dict(color=PURPLE, width=2), marker=dict(size=6)))
        fig.add_trace(go.Scatter(x=tmp[dc], y=trend_vals, mode="lines", name="Trend",
            line=dict(color="#764ba2", width=1.5, dash="dot")))
        fig.add_trace(go.Scatter(x=future_dates, y=future_vals, mode="lines+markers", name="Forecast",
            line=dict(color="#f093fb", width=2, dash="dash"), marker=dict(size=7, symbol="diamond")))
        fig.add_vrect(x0=tmp[dc].max(), x1=future_dates.max(),
            fillcolor="rgba(240,147,251,0.06)", line_width=0,
            annotation_text="Forecast zone", annotation_position="top left",
            annotation_font_size=10, annotation_font_color="#9ca3af")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,249,255,0.6)",
            font=dict(family="Inter", size=11, color="#374151"),
            margin=dict(t=45, b=30, l=30, r=20), height=340,
            title=dict(text=f"🔮 {nc} Forecast (Linear Trend)", font=dict(size=13, color="#1a202c")),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig.update_xaxes(showgrid=False, linecolor="#e5e7eb")
        fig.update_yaxes(gridcolor="#f0f0f0", linecolor="#e5e7eb")
        return fig
    except Exception:
        return None


# ── SIDEBAR ─────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 DataMind AI")
    st.markdown("---")
    st.markdown("**🔑 API Key**")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...",
                             label_visibility="collapsed", help="Free at console.groq.com")
    st.markdown("---")
    st.markdown("**📁 Dataset**")
    uploaded_file = st.file_uploader("CSV or Excel", type=["csv","xlsx","xls"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**⚙️ Report Settings**")
    report_title    = st.text_input("Report Title", value="Business Intelligence Report")
    company_name    = st.text_input("Company / Project", value="My Organization")
    analyst_name    = st.text_input("Prepared By", value="Data Analyst")
    report_tone     = st.selectbox("Tone", ["Professional","Executive","Technical","Simplified"])
    report_industry = st.selectbox("Industry", ["General","Retail / E-Commerce","Finance / Banking",
                                                 "Healthcare","Manufacturing","SaaS / Tech","HR / People Analytics"])
    st.markdown("---")
    st.caption("1. Enter API key\n2. Upload CSV/Excel\n3. Fill settings\n4. Generate report\n5. Chat with data\n6. Download PDF")


# ── HERO ────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">✦ Powered by Groq LLaMA 3.3 · 70B</div>
    <h1>DataMind <span>AI</span></h1>
    <p>Upload any dataset → Full AI business report, interactive charts, forecasts &amp; PDF in seconds</p>
    <div class="hero-pills">
        <span class="hero-pill">🤖 AI Executive Summary</span>
        <span class="hero-pill">📊 Smart Visualizations</span>
        <span class="hero-pill">🔮 Trend Forecasting</span>
        <span class="hero-pill">💬 Chat With Your Data</span>
        <span class="hero-pill">🏥 Data Health Score</span>
        <span class="hero-pill">📄 PDF Download</span>
    </div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.info("👈 **Step 1:** Enter your free Groq API key in the sidebar — get one at [console.groq.com](https://console.groq.com)")
    c1, c2, c3 = st.columns(3)
    for col, icon, label in [(c1,"🤖","AI-Written Report"),(c2,"📊","6 Smart Charts"),(c3,"💬","Chat With Data")]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-icon">{icon}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.stop()

if not uploaded_file:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#f8f9ff,#f0f4ff);border:2px dashed #667eea;
        border-radius:16px;padding:3rem 2rem;text-align:center;margin-top:1rem;">
        <div style="font-size:2.5rem;margin-bottom:0.75rem;">⬆️</div>
        <h3 style="color:#667eea;margin:0 0 0.4rem;">Upload Your Dataset</h3>
        <p style="color:#9ca3af;margin:0;font-size:0.9rem;">CSV · XLSX · XLS &nbsp;|&nbsp; Any business data works</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"❌ Could not read file: {e}")
    st.stop()

if df.empty:
    st.error("❌ Uploaded file is empty.")
    st.stop()

df.columns = df.columns.str.strip()
df = df.dropna(how="all").reset_index(drop=True)
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
cat_cols     = df.select_dtypes(include=["object","category"]).columns.tolist()
missing_pct  = round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 1)

st.markdown("""<div class="section-hdr">
    <div class="section-hdr-icon">📋</div>
    <h2>Dataset Overview</h2>
    <span>— quick snapshot of your uploaded file</span>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card"><div class="metric-icon">📦</div><div class="metric-num">{df.shape[0]:,}</div><div class="metric-label">Rows</div></div>
    <div class="metric-card"><div class="metric-icon">📐</div><div class="metric-num">{df.shape[1]}</div><div class="metric-label">Columns</div></div>
    <div class="metric-card"><div class="metric-icon">🔢</div><div class="metric-num">{len(numeric_cols)}</div><div class="metric-label">Numeric Cols</div></div>
    <div class="metric-card"><div class="metric-icon">🏷️</div><div class="metric-num">{len(cat_cols)}</div><div class="metric-label">Category Cols</div></div>
    <div class="metric-card"><div class="metric-icon">{"✅" if missing_pct==0 else "⚠️"}</div>
        <div class="metric-num" style="color:{'#10b981' if missing_pct==0 else '#f59e0b'}">{missing_pct}%</div>
        <div class="metric-label">Missing Data</div></div>
</div>""", unsafe_allow_html=True)

with st.expander("👀 Preview Data"):
    st.dataframe(df.head(50), use_container_width=True)
with st.expander("📐 Column Info"):
    st.dataframe(pd.DataFrame({
        "Column": df.columns, "Type": df.dtypes.values,
        "Non-Null": df.notnull().sum().values,
        "Missing": df.isnull().sum().values,
        "Missing %": (df.isnull().sum()/len(df)*100).round(1).values,
        "Unique": df.nunique().values,
    }), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("🚀 Generate Full AI Report", use_container_width=True)

if not generate_btn and "report_generated" not in st.session_state:
    st.stop()

if generate_btn or "report_generated" not in st.session_state:
    try:
        client = init_groq(api_key)
    except Exception:
        st.error("❌ Invalid Groq API key.")
        st.stop()

    progress = st.progress(0, text="🔍 Analyzing dataset structure…")
    stats_summary = analyze_dataframe(df)
    anomalies     = detect_anomalies(df)
    col_insights  = get_column_insights(df)
    health_score, health_grade, health_class = compute_health_score(df, anomalies)

    sys_p = f"""You are a senior data analyst writing a {report_tone.lower()} business report for the {report_industry} industry.
Reference actual column names and real numbers. Write clear business English. No markdown asterisks, headers, or bullet symbols."""

    progress.progress(15, text="🤖 Writing Executive Summary…")
    exec_summary = call_groq(client, f"""Write a 3-paragraph executive summary.
Dataset: {df.shape[0]} rows, {df.shape[1]} columns. File: {uploaded_file.name}
Columns: {list(df.columns[:20])}. Numeric: {numeric_cols[:10]}. Categories: {cat_cols[:10]}
Stats: {json.dumps(stats_summary.get('key_stats',{}), default=str)[:1200]}
Company: {company_name}. Industry: {report_industry}
Para1: scope and what dataset covers. Para2: key patterns with numbers. Para3: business implications.""", sys_p, 700)

    progress.progress(30, text="🤖 Identifying key findings…")
    key_findings = call_groq(client, f"""Write exactly 5 key findings, numbered 1-5.
Each: number, period, space, title (no bold markers), colon, 2 sentences with specific column names and numbers.
Stats: {json.dumps(stats_summary, default=str)[:2000]}
Insights: {json.dumps(col_insights, default=str)[:1500]}
Columns: {list(df.columns)}""", sys_p, 750)

    progress.progress(45, text="🤖 Detecting anomalies…")
    anomaly_narrative = call_groq(client, f"""Explain these anomalies and their business significance.
Anomalies: {json.dumps(anomalies, default=str)[:1500]}
Dataset: {df.shape[0]} rows, columns: {list(df.columns[:15])}
Write 3-5 short paragraphs. Each: one anomaly, its nature, business impact.""", sys_p, 600)

    progress.progress(58, text="🤖 Writing recommendations…")
    recommendations = call_groq(client, f"""Write exactly 5 actionable recommendations, numbered 1-5.
Each: number, period, space, action title, colon, 2 sentences — specific and actionable with data references.
Findings: {key_findings[:800]}. Anomalies: {json.dumps(anomalies, default=str)[:600]}. Industry: {report_industry}""", sys_p, 700)

    progress.progress(70, text="🧠 Computing health score commentary…")
    health_commentary = call_groq(client, f"""In 2 sentences explain this data health score of {health_score}/100 (grade: {health_grade}).
Mention: missing data {missing_pct}%, {len(anomalies.get('outliers',{}))} columns with outliers, {anomalies.get('duplicate_rows',{}).get('count',0)} duplicate rows.
Be specific and {report_tone.lower()}. No markdown.""", sys_p, 200)

    progress.progress(82, text="📊 Building charts…")
    charts       = build_charts(df)
    forecast_fig = build_forecast_chart(df)

    progress.progress(93, text="📄 Generating PDF…")
    pdf_bytes = generate_pdf_report(
        title=report_title, company=company_name, analyst=analyst_name,
        filename=uploaded_file.name, df=df,
        exec_summary=exec_summary, key_findings=key_findings,
        anomaly_narrative=anomaly_narrative, recommendations=recommendations,
        stats_summary=stats_summary, anomalies=anomalies,
        charts=charts, tone=report_tone,
    )

    progress.progress(100, text="✅ Report ready!")
    import time; time.sleep(0.3)
    progress.empty()

    st.session_state.update({
        "report_generated": True,
        "exec_summary": exec_summary,
        "key_findings": key_findings,
        "anomaly_narrative": anomaly_narrative,
        "recommendations": recommendations,
        "health_score": health_score,
        "health_grade": health_grade,
        "health_class": health_class,
        "health_commentary": health_commentary,
        "stats_summary": stats_summary,
        "anomalies": anomalies,
        "charts": charts,
        "forecast_fig": forecast_fig,
        "pdf_bytes": pdf_bytes,
        "chat_history": [],
        "groq_client": client,
        "df_context": json.dumps({
            "columns": list(df.columns),
            "shape": [int(df.shape[0]), int(df.shape[1])],
            "key_stats": stats_summary.get("key_stats", {}),
            "cat_stats": stats_summary.get("cat_stats", {}),
            "anomalies": {k: str(v)[:200] for k, v in anomalies.items()},
            "correlations": stats_summary.get("strong_correlations", []),
        }, default=str)[:3000],
    })

exec_summary      = st.session_state.exec_summary
key_findings      = st.session_state.key_findings
anomaly_narrative = st.session_state.anomaly_narrative
recommendations   = st.session_state.recommendations
health_score      = st.session_state.health_score
health_grade      = st.session_state.health_grade
health_class      = st.session_state.health_class
health_commentary = st.session_state.health_commentary
anomalies         = st.session_state.anomalies
charts            = st.session_state.charts
forecast_fig      = st.session_state.forecast_fig
pdf_bytes         = st.session_state.pdf_bytes

st.success("✅ Your AI Report is ready! Explore the tabs below.")

st.markdown(f"""
<div class="health-box {health_class}">
    <div class="health-score-circle">{health_score}</div>
    <div class="health-text">
        <h3>Data Health Score: {health_grade}</h3>
        <p>{health_commentary}</p>
    </div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Summary & Findings","📊 Charts","🔮 Forecast",
    "⚠️ Anomalies","✅ Recommendations","💬 Chat With Data",
])

with tab1:
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">📝</div><h2>Executive Summary</h2></div>""", unsafe_allow_html=True)
    for para in exec_summary.split("\n"):
        if para.strip():
            st.markdown(f'<div class="card">{para.strip()}</div>', unsafe_allow_html=True)
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">🔍</div><h2>Key Findings</h2></div>""", unsafe_allow_html=True)
    lines = [l.strip() for l in key_findings.split("\n") if l.strip() and len(l.strip()) > 5]
    for i, line in enumerate(lines):
        is_num = len(line) > 1 and line[0].isdigit()
        cls = "card card-finding" if is_num else "card"
        nbadge = f'<span class="finding-num">{i+1}</span>' if is_num else ""
        st.markdown(f'<div class="{cls}">{nbadge}{line}</div>', unsafe_allow_html=True)
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">📐</div><h2>Statistical Summary</h2></div>""", unsafe_allow_html=True)
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)

with tab2:
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">📊</div><h2>Visualizations</h2><span>— auto-built from your data types</span></div>""", unsafe_allow_html=True)
    if charts:
        for i in range(0, len(charts), 2):
            if i + 1 < len(charts):
                c1, c2 = st.columns(2)
                with c1: st.plotly_chart(charts[i],   use_container_width=True)
                with c2: st.plotly_chart(charts[i+1], use_container_width=True)
            else:
                st.plotly_chart(charts[i], use_container_width=True)
    else:
        st.info("Not enough numeric data for charts.")

with tab3:
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">🔮</div><h2>Trend Forecast <span class="forecast-badge">Linear Regression</span></h2></div>""", unsafe_allow_html=True)
    if forecast_fig:
        st.plotly_chart(forecast_fig, use_container_width=True)
        st.markdown("""<div class="card" style="font-size:0.85rem;color:#9ca3af;border-color:#f0f0f0;">
            ⚠️ <strong>Disclaimer:</strong> Linear regression forecast — directional indicator only. Not a financial prediction.</div>""", unsafe_allow_html=True)
    else:
        st.info("📅 Forecasting needs at least one date column + one numeric column with 4+ rows.")

with tab4:
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">⚠️</div><h2>Anomalies & Data Quality</h2></div>""", unsafe_allow_html=True)
    lines = [a.strip() for a in anomaly_narrative.split("\n") if a.strip()]
    for line in lines:
        sev = "badge-high" if any(w in line.lower() for w in ["extreme","critical","significant","major"]) \
              else "badge-medium" if any(w in line.lower() for w in ["moderate","warning","missing","outlier"]) \
              else "badge-low"
        label = "High" if sev=="badge-high" else "Medium" if sev=="badge-medium" else "Low"
        st.markdown(f'<div class="card card-anomaly">{line} <span class="badge {sev}">{label}</span></div>', unsafe_allow_html=True)
    outliers = anomalies.get("outliers", {})
    if outliers:
        st.markdown("""<div class="section-hdr" style="margin-top:1.5rem;"><div class="section-hdr-icon">📋</div><h2>Outlier Detail</h2></div>""", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([
            {"Column": col, "Outlier Count": v["count"], "Outlier %": f"{v['pct']}%",
             "Lower Bound": v["lower_bound"], "Upper Bound": v["upper_bound"],
             "Data Min": v["extreme_min"], "Data Max": v["extreme_max"]}
            for col, v in outliers.items()
        ]), use_container_width=True)

with tab5:
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">✅</div><h2>Actionable Recommendations</h2></div>""", unsafe_allow_html=True)
    rlines = [r.strip() for r in recommendations.split("\n") if r.strip() and len(r.strip()) > 5]
    for i, reco in enumerate(rlines):
        nb = f'<span class="reco-num">{i+1}</span>' if reco[0].isdigit() else ""
        st.markdown(f'<div class="card card-reco">{nb}{reco}</div>', unsafe_allow_html=True)

with tab6:
    st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">💬</div><h2>Chat With Your Data</h2><span>— ask anything about this dataset</span></div>""", unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:0.85rem;color:#9ca3af;margin-bottom:0.5rem;">💡 Try these:</p>
    <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
        <span style="background:#f0f4ff;border:1px solid #c7d2fe;color:#667eea;font-size:0.8rem;padding:0.35rem 0.85rem;border-radius:999px;">Which column has the highest variability?</span>
        <span style="background:#f0f4ff;border:1px solid #c7d2fe;color:#667eea;font-size:0.8rem;padding:0.35rem 0.85rem;border-radius:999px;">What is the biggest business risk here?</span>
        <span style="background:#f0f4ff;border:1px solid #c7d2fe;color:#667eea;font-size:0.8rem;padding:0.35rem 0.85rem;border-radius:999px;">Which category performs best?</span>
        <span style="background:#f0f4ff;border:1px solid #c7d2fe;color:#667eea;font-size:0.8rem;padding:0.35rem 0.85rem;border-radius:999px;">Summarize this data in one sentence.</span>
    </div>""", unsafe_allow_html=True)

    if st.session_state.get("chat_history"):
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="chat-msg-user"><div class="bubble">{msg["content"]}</div></div>'
            else:
                chat_html += f'<div class="chat-msg-ai"><div class="chat-avatar">AI</div><div class="bubble">{msg["content"]}</div></div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    user_q = st.text_input("Ask a question about your data…", placeholder="e.g. Which region has the highest sales?", key="chat_input")
    col_send, col_clear = st.columns([5, 1])
    with col_send:
        send = st.button("Send ↗", use_container_width=True)
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if send and user_q.strip():
        chat_sys = f"""You are a senior data analyst. Answer questions about this specific dataset only.
Be concise, specific, reference actual numbers and column names.
Dataset: {st.session_state.df_context}
Summary: {exec_summary[:400]}
Findings: {key_findings[:400]}
Write plain conversational text. No markdown asterisks or headers."""
        msgs = [{"role": "system", "content": chat_sys}]
        for h in st.session_state.chat_history[-6:]:
            msgs.append(h)
        msgs.append({"role": "user", "content": user_q})
        with st.spinner("Thinking…"):
            try:
                resp = st.session_state.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile", messages=msgs, temperature=0.3, max_tokens=500)
                answer = resp.choices[0].message.content.strip()
            except Exception as e:
                answer = f"Sorry, error: {e}"
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

st.markdown("---")
st.markdown("""<div class="section-hdr"><div class="section-hdr-icon">📥</div><h2>Download Report</h2></div>""", unsafe_allow_html=True)
safe_title = report_title.replace(" ","_").replace("/","-")
st.markdown('<div class="download-btn">', unsafe_allow_html=True)
st.download_button(
    label="📥 Download Full PDF Report",
    data=pdf_bytes,
    file_name=f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf",
    use_container_width=True,
)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="footer">
    <strong>DataMind AI</strong> &nbsp;·&nbsp;
    {datetime.now().strftime('%B %d, %Y')} &nbsp;·&nbsp;
    Groq LLaMA 3.3 · 70B + Streamlit &nbsp;·&nbsp;
    {df.shape[0]:,} rows &times; {df.shape[1]} cols analysed
</div>""", unsafe_allow_html=True)
