import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="2010s NHL Champion Analysis",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

SEASON_LABELS = {
    "20082009": "2008-09", "20092010": "2009-10", "20102011": "2010-11",
    "20112012": "2011-12", "20122013": "2012-13", "20132014": "2013-14",
    "20142015": "2014-15", "20152016": "2015-16", "20162017": "2016-17",
    "20172018": "2017-18", "20182019": "2018-19",
}

CHAMPIONS = {
    "20082009": "PIT", "20092010": "CHI", "20102011": "BOS",
    "20112012": "LAK", "20122013": "CHI", "20132014": "LAK",
    "20142015": "CHI", "20152016": "PIT", "20162017": "PIT",
    "20172018": "WSH", "20182019": "STL",
}

METRICS = [
    ("penaltyKillPct",  "PK%"),
    ("powerPlayPct",    "PP%"),
    ("xG_pct",          "xG%"),
    ("finishing_rate",  "Finishing Rate"),
    ("GSAx",            "GSAx"),
    ("shotsForPerGame", "Shots For/G"),
]

COLORS = {
    "champion":    "#e8a838",
    "average":     "#4a90d9",
    "background":  "#0e1117",
    "card":        "#1c1f26",
    "positive":    "#4caf50",
    "negative":    "#f44336",
}

# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------

@st.cache_data
def load_data():
    db_path = Path("nhl_master.db")
    if not db_path.exists():
        st.error("nhl_master.db not found. Make sure it's in the same directory as this app.")
        st.stop()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM team_seasons", conn)
    conn.close()
    return df

df = load_data()

# Filter metrics to only those present in the dataframe
METRICS = [(col, lbl) for col, lbl in METRICS if col in df.columns]
METRIC_COLS = [col for col, _ in METRICS]
METRIC_LBLS = [lbl for _, _ in METRICS]

# Precompute normalization ranges
col_min = {col: df[col].min() for col in METRIC_COLS}
col_max = {col: df[col].max() for col in METRIC_COLS}

def norm(col, val):
    rng = col_max[col] - col_min[col]
    return float((val - col_min[col]) / rng) if rng != 0 else 0.5

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🏒 2010s NHL Analysis")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🏆 Champion Dashboard", "📊 Correlation Heatmap", "📈 Champion Rankings", "📖 About"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown(
        "<small>Data: NHL API via nhl-api-py<br>Seasons: 2008–2019</small>",
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# PAGE 1 — CHAMPION DASHBOARD
# -----------------------------------------------------------------------------

if page == "🏆 Champion Dashboard":

    st.title("🏆 Stanley Cup Champion Dashboard")
    st.markdown("Compare any champion's stats against the average team from any season.")
    st.markdown("---")

    # Controls
    col1, col2, col3 = st.columns([2, 1.5, 1])

    # Build champion options
    champ_options = {}
    for season, abbrev in CHAMPIONS.items():
        row = df[
            (df["season"] == season) &
            (df["is_champion"] == 1) &
            (df["stage"] == "playoffs")
        ]
        if not row.empty:
            name = row["teamFullName"].iloc[0]
            label = f"{SEASON_LABELS[season]} — {name}"
            champ_options[label] = season

    with col1:
        selected_champ_label = st.selectbox("🏆 Champion", list(champ_options.keys()))
    with col2:
        selected_cmp_label = st.selectbox(
            "📅 Compare against season",
            [v for v in SEASON_LABELS.values()]
        )
    with col3:
        selected_stage = st.radio("🏟 Stage", ["regular", "playoffs"], horizontal=True)

    # Resolve keys
    champ_season = champ_options[selected_champ_label]
    cmp_season   = {v: k for k, v in SEASON_LABELS.items()}[selected_cmp_label]

    # Fetch data
    champ_row = df[
        (df["season"] == champ_season) &
        (df["is_champion"] == 1) &
        (df["stage"] == selected_stage)
    ]
    avg_row = df[
        (df["season"] == cmp_season) &
        (df["stage"] == selected_stage)
    ][METRIC_COLS].mean()

    if champ_row.empty:
        st.warning(f"No {selected_stage} data found for this champion. Try switching stage.")
        st.stop()

    champ_vals = champ_row[METRIC_COLS].iloc[0]
    champ_name = champ_row["teamFullName"].iloc[0]
    cmp_label  = f"Avg team — {selected_cmp_label}"

    # Normalize
    c_norm = [norm(col, champ_vals[col]) for col in METRIC_COLS]
    a_norm = [norm(col, avg_row[col])    for col in METRIC_COLS]

    lbls_loop = METRIC_LBLS + [METRIC_LBLS[0]]
    c_loop    = c_norm      + [c_norm[0]]
    a_loop    = a_norm      + [a_norm[0]]

    st.markdown("---")

    # Radar + table layout
    radar_col, table_col = st.columns([1.2, 1])

    with radar_col:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=c_loop, theta=lbls_loop,
            fill="toself", name=champ_name,
            line=dict(color=COLORS["champion"], width=2),
            fillcolor="rgba(232,168,56,0.2)"
        ))
        fig.add_trace(go.Scatterpolar(
            r=a_loop, theta=lbls_loop,
            fill="toself", name=cmp_label,
            line=dict(color=COLORS["average"], width=2),
            fillcolor="rgba(74,144,217,0.15)"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            template="plotly_dark",
            legend=dict(x=0.8, y=1.15),
            margin=dict(t=40, b=20),
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)

    with table_col:
        st.markdown(f"#### {champ_name} vs {cmp_label}")
        st.caption(f"Stage: {selected_stage.capitalize()} · Normalized 0–1 across all seasons")

        rows = []
        for col, lbl in METRICS:
            c_val = round(float(champ_vals[col]), 3)
            a_val = round(float(avg_row[col]), 3)
            delta = round(c_val - a_val, 3)
            rows.append({
                "Metric":       lbl,
                champ_name:     c_val,
                cmp_label:      a_val,
                "Δ Delta":      delta,
            })

        df_table = pd.DataFrame(rows)

        def color_delta(val):
            if isinstance(val, float):
                return f"color: {COLORS['positive']}" if val > 0 else f"color: {COLORS['negative']}"
            return ""

        st.dataframe(
            df_table.style.applymap(color_delta, subset=["Δ Delta"]),
            hide_index=True,
            use_container_width=True
        )

        # Quick metric cards
        st.markdown("---")
        st.markdown("**Champion edges:**")
        positive = [r["Metric"] for r in rows if r["Δ Delta"] > 0]
        negative = [r["Metric"] for r in rows if r["Δ Delta"] < 0]
        if positive:
            st.success(f"Above average: {', '.join(positive)}")
        if negative:
            st.error(f"Below average: {', '.join(negative)}")

# -----------------------------------------------------------------------------
# PAGE 2 — CORRELATION HEATMAP
# -----------------------------------------------------------------------------

elif page == "📊 Correlation Heatmap":

    st.title("📊 Correlation Heatmap")
    st.markdown("How strongly does each metric correlate with winning the Stanley Cup?")
    st.markdown("---")

    stage_filter = st.radio("Stage", ["regular", "playoffs"], horizontal=True)

    df_stage = df[df["stage"] == stage_filter].copy()
    corr_cols = ["is_champion"] + METRIC_COLS
    corr_cols = [c for c in corr_cols if c in df_stage.columns]
    corr = df_stage[corr_cols].corr().round(2)

    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title=f"Correlation Heatmap — {stage_filter.capitalize()} Season",
        template="plotly_dark",
        aspect="auto"
    )
    fig.update_layout(height=550, margin=dict(t=60))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Key takeaway")
    st.info(
        "**GSAx (0.27)** is the strongest correlator with championship outcome. "
        "PK% and PP% — the original hypothesis — come in at 0.09 and 0.03 respectively. "
        "Elite metrics define the field of contention, but don't predict the winner."
    )

# -----------------------------------------------------------------------------
# PAGE 3 — CHAMPION RANKINGS
# -----------------------------------------------------------------------------

elif page == "📈 Champion Rankings":

    st.title("📈 Champion Rankings")
    st.markdown(
        "Where did each champion rank among all playoff teams in a given metric? "
        "Gold = top 4. Red = outside top 4."
    )
    st.markdown("---")

    metric_choice = st.selectbox(
        "Metric",
        options=[lbl for _, lbl in METRICS],
        index=0
    )
    metric_col = METRIC_COLS[[lbl for _, lbl in METRICS].index(metric_choice)]

    df_post = df[df["stage"] == "playoffs"].copy()
    seasons_sorted = sorted(df_post["season"].unique())

    ranks, names, totals, colors_list = [], [], [], []

    for season in seasons_sorted:
        df_s = df_post[df_post["season"] == season].copy()
        df_s["rank"] = df_s[metric_col].rank(ascending=False, method="min")
        champ = df_s[df_s["is_champion"] == 1]
        if champ.empty:
            continue
        r    = int(champ["rank"].iloc[0])
        name = champ["teamFullName"].iloc[0]
        ranks.append(r)
        names.append(name)
        totals.append(len(df_s))
        colors_list.append(COLORS["champion"] if r <= 4 else COLORS["negative"])

    season_lbls = [SEASON_LABELS[s] for s in seasons_sorted if not df_post[
        (df_post["season"] == s) & (df_post["is_champion"] == 1)].empty]

    fig = go.Figure()

    # Field bars
    fig.add_trace(go.Bar(
        x=season_lbls, y=totals,
        marker_color="#2a3a4a", name="Total playoff teams",
        hoverinfo="skip"
    ))
    # Champion rank bars
    fig.add_trace(go.Bar(
        x=season_lbls, y=ranks,
        marker_color=colors_list,
        name="Champion rank",
        text=[f"#{r} — {n}" for r, n in zip(ranks, names)],
        textposition="outside",
        hovertemplate="%{text}<extra></extra>"
    ))
    # Top 4 line
    fig.add_hline(y=4, line_dash="dash", line_color="white",
                  opacity=0.5, annotation_text="Top 4 threshold")

    fig.update_layout(
        barmode="overlay",
        yaxis=dict(autorange="reversed", title="Rank (1 = best)", dtick=1),
        template="plotly_dark",
        title=f"Champion rank in {metric_choice} — Playoffs",
        legend=dict(x=0.01, y=0.99),
        height=500,
        margin=dict(t=60)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.markdown("---")
    st.markdown("### Full ranking table")
    summary = pd.DataFrame({
        "Season":   season_lbls,
        "Champion": names,
        f"Rank ({metric_choice})": [f"#{r} / {t}" for r, t in zip(ranks, totals)],
        "Top 4?":   ["✅" if r <= 4 else "❌" for r in ranks]
    })
    st.dataframe(summary, hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 4 — ABOUT
# -----------------------------------------------------------------------------

elif page == "📖 About":

    st.title("📖 About this project")

    st.markdown("""
    ### The question

    A tweet claimed the last 10 Stanley Cup winners all ranked top-12 in PP%, PK%, xGF%,
    xGA% and 5v5 SV%. The implication: championships are predictable.
    I pulled 11 seasons of NHL data to find out if that holds up.

    ### The data

    - **Source:** NHL API via [`nhl-api-py`](https://github.com/coreyjs/nhl-api-py)
    - **Scope:** All 30 teams, 2008–2019, regular season + playoffs
    - **Storage:** SQLite — one row per team, per season, per stage
    - **Metrics:** PK%, PP%, xG%, xG/G, GSAx, Finishing Rate, Net xG/G

    ### Key findings

    - **GSAx (r=0.27)** is the strongest correlator with championship outcome
    - **PK% (0.09) and PP% (0.03)** show negligible correlation
    - Champions are almost always elite — but so are teams eliminated in round 2
    - Being elite is **necessary, not sufficient**
    - The dynasty exception: Chicago 3× in 5 years, Pittsburgh back-to-back

    ### Stack

    `Python` · `pandas` · `SQLite` · `nhl-api-py` · `Plotly` · `seaborn` · `Streamlit`

    ### Why 2008–2019?

    NHL 2K10 is a banger of a videogame. Also: Crosby's three Cups, Ovi finally getting his,
    Kane's dynasty run with Chicago — it's the most interesting window of modern NHL history
    for this kind of analysis.
    """)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("📓 View Notebook", "https://github.com/LuccaParodi/Nhl_Data_AnalysisProject")  
    with col2:
        st.link_button("💼 LinkedIn", "https://linkedin.com/in/lucca-parodi-3bb1ba2b2")    
