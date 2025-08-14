
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import base64
from io import BytesIO

st.set_page_config(page_title="매출 대시보드", layout="wide")

st.title("📊 매출 대시보드 (Streamlit)")
st.caption("바차트·히스토그램 · 시계열 · 파이 · 산점도 · 파레토 — 업로드 폰트 적용 가능")

# --- Sidebar: file uploads ---
st.sidebar.header("1) 데이터 / 폰트 업로드")
excel_file = st.sidebar.file_uploader("엑셀 파일 업로드 (시트: 바차트_히스토그램, 시계열차트, 파이차트, 산점도, 파레토차트)", type=["xlsx"])
font_file = st.sidebar.file_uploader("선택: NanumGothic 등 TTF 폰트 업로드 (한글 깨짐 방지)", type=["ttf"])

# Inject font via base64 if provided
if font_file is not None:
    font_bytes = font_file.read()
    font_b64 = base64.b64encode(font_bytes).decode("ascii")
    font_name = "UploadedFont"
    st.markdown(f"""
        <style>
        @font-face {{
            font-family: '{font_name}';
            src: url(data:font/ttf;base64,{font_b64}) format('truetype');
            font-weight: normal;
            font-style: normal;
            font-display: swap;
        }}
        html, body, [class*="css"]  {{
            font-family: '{font_name}', -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        }}
        </style>
    """, unsafe_allow_html=True)
else:
    font_name = "-apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"

# Helper to format y-axis tick labels with thousands separator
def korean_number(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return x

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df_bar_hist = pd.read_excel(xls, sheet_name='바차트_히스토그램')
    df_timeseries = pd.read_excel(xls, sheet_name='시계열차트')
    df_pie = pd.read_excel(xls, sheet_name='파이차트')
    df_scatter = pd.read_excel(xls, sheet_name='산점도')
    df_pareto = pd.read_excel(xls, sheet_name='파레토차트')

    # Date formatting
    df_bar_hist['월'] = pd.to_datetime(df_bar_hist['월'])
    df_bar_hist['월_str'] = df_bar_hist['월'].dt.strftime("%Y-%m")
    df_timeseries['월'] = pd.to_datetime(df_timeseries['월'])
    df_timeseries['월_str'] = df_timeseries['월'].dt.strftime("%Y-%m")

    return df_bar_hist, df_timeseries, df_pie, df_scatter, df_pareto

if excel_file is None:
    st.info("왼쪽 사이드바에서 엑셀 파일을 업로드하세요.")
    st.stop()

df_bar_hist, df_timeseries, df_pie, df_scatter, df_pareto = load_data(excel_file)

# --- Layout: 3 rows ---
# Row 1: Bar + Hist
c1, c2 = st.columns(2)
with c1:
    st.subheader("월별 총 매출 (바차트)")
    fig_bar = go.Figure(data=[
        go.Bar(x=df_bar_hist['월_str'], y=df_bar_hist['총 매출'],
               hovertemplate="%{x}<br>매출: %{y:,}원<extra></extra>")
    ])
    fig_bar.update_layout(margin=dict(l=40, r=10, t=30, b=40),
                          yaxis_title="총 매출", xaxis_title="월",
                          font=dict(family=font_name, size=12))
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("총 매출 분포 (히스토그램)")
    fig_hist = go.Figure(data=[
        go.Histogram(x=df_bar_hist['총 매출'], nbinsx=8,
                     hovertemplate="매출: %{x:,}원 (빈도 %{y})<extra></extra>")
    ])
    fig_hist.update_layout(margin=dict(l=40, r=10, t=30, b=40),
                           xaxis_title="총 매출", yaxis_title="빈도",
                           font=dict(family=font_name, size=12))
    st.plotly_chart(fig_hist, use_container_width=True)

# Row 2: Time series (full width)
st.subheader("제품별 월별 매출 (시계열)")
ts_cols = [c for c in df_timeseries.columns if c not in ['월', '월_str']]
fig_ts = go.Figure()
for col in ts_cols:
    fig_ts.add_trace(go.Scatter(
        x=df_timeseries['월_str'], y=df_timeseries[col],
        mode="lines+markers", name=col,
        hovertemplate="%{x}<br>" + col + ": %{y:,}원<extra></extra>"
    ))
fig_ts.update_layout(margin=dict(l=40, r=10, t=30, b=40),
                     xaxis_title="월", yaxis_title="매출",
                     legend=dict(orientation='h', x=0, y=1.12),
                     font=dict(family=font_name, size=12))
st.plotly_chart(fig_ts, use_container_width=True)

# Row 3: Pie + Scatter
c3, c4 = st.columns(2)
with c3:
    st.subheader("1분기 제품별 매출 비율 (파이차트)")
    labels = df_pie['Unnamed: 0']
    values = df_pie['1분기 매출']
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3,
                                     textinfo="label+percent",
                                     hovertemplate="%{label}<br>%{value:,}원<extra></extra>")])
    fig_pie.update_layout(margin=dict(l=40, r=10, t=30, b=40),
                          showlegend=False,
                          font=dict(family=font_name, size=12))
    st.plotly_chart(fig_pie, use_container_width=True)

with c4:
    st.subheader("제품 A 매출 vs 비용 (산점도)")
    fig_scatter = go.Figure(data=[
        go.Scatter(x=df_scatter['제품 A 매출'], y=df_scatter['비용'],
                   mode="markers",
                   hovertemplate="매출 %{x:,}원<br>비용 %{y:,}원<extra></extra>")
    ])
    fig_scatter.update_layout(margin=dict(l=40, r=10, t=30, b=40),
                              xaxis_title="제품 A 매출", yaxis_title="비용",
                              font=dict(family=font_name, size=12))
    st.plotly_chart(fig_scatter, use_container_width=True)

# Row 4: Pareto (full width)
st.subheader("부서별 매출과 누적비율 (파레토)")
df_pareto_sorted = df_pareto.sort_values(by='매출', ascending=False).reset_index(drop=True)
df_pareto_sorted['누적비율'] = (df_pareto_sorted['매출'].cumsum() / df_pareto_sorted['매출'].sum() * 100).round(2)

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(x=df_pareto_sorted['부서'], y=df_pareto_sorted['매출'], name='매출',
                            hovertemplate="%{x}<br>매출 %{y:,}원<extra></extra>"))
fig_pareto.add_trace(go.Scatter(x=df_pareto_sorted['부서'], y=df_pareto_sorted['누적비율'],
                                name='누적 비율', mode='lines+markers', yaxis='y2',
                                hovertemplate="%{x}<br>누적 %{y:.1f}%<extra></extra>"))
fig_pareto.update_layout(
    margin=dict(l=40, r=40, t=30, b=40),
    xaxis_title="부서",
    yaxis=dict(title="매출"),
    yaxis2=dict(title="누적 비율(%)", overlaying='y', side='right', range=[0, 110]),
    legend=dict(orientation='h', x=0, y=1.12),
    font=dict(family=font_name, size=12)
)
st.plotly_chart(fig_pareto, use_container_width=True)

# Optional: Show raw tables
with st.expander("원본 데이터 미리보기"):
    st.write("바차트_히스토그램", df_bar_hist.head())
    st.write("시계열차트", df_timeseries.head())
    st.write("파이차트", df_pie.head())
    st.write("산점도", df_scatter.head())
    st.write("파레토차트", df_pareto.head())

st.success("완료: 업로드한 폰트가 있으면 대시보드 전체에 적용됩니다.")




