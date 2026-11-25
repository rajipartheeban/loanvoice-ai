"""
LoanVoice AI - Streamlit app (version 3: QuickCart-style layout, colour per problem)

    streamlit run app/streamlit_app.py

Pages (tabs at the top)
    Overview            - KPI tiles with trends, the 3 problems to fix first, complaint mix, release lesson
    Compare apps        - each app's rating trend and complaint profile
    Issue explorer      - one problem in depth, with the reviews behind it
    What if we fix it?  - simulator: one-star reviews prevented and rating gain
    Roadmap             - the 3-month plan and the priority ranking
    How it works        - data coverage, model accuracy, statistics, limits
    Ask the reviews     - search the reviews in plain English (optional LLM)

Reads the labelled reviews from the database (view v_review_issues) and the
results in outputs/ written by `python pipeline.py run`.
"""
import html
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from loanvoice import db  # noqa: E402
from loanvoice.assistant import ReviewSearch, data_summary, llm_answer, monthly_brief  # noqa: E402
from loanvoice.config import (DEFAULT_FIX_RATE, EFFORT_POINTS, ISSUES, OUTPUT_DIR,  # noqa: E402
                              PROBLEM_ISSUES, PROPOSED_FIX)
from loanvoice.impact import rating_gain_table  # noqa: E402

st.set_page_config(page_title="LoanVoice AI", page_icon="💬", layout="wide")

# ---------------------------------------------------------------- colours
BG, SURFACE, BORDER = "#161a19", "#1d2221", "#2c3331"
TEXT, TEXT_2, MUTED = "#eef1f0", "#b3bcb9", "#5c6663"
TEAL, GOOD, BAD = "#2bb3a3", "#3fbf7f", "#f26d6d"
# Validated categorical palette (dark mode). Each problem keeps its colour on every page.
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"]
PCOLOR = {k: SERIES[i] for i, k in enumerate(PROBLEM_ISSUES)}
PCOLOR.update({"positive": TEAL, "other": MUTED})
LCOLOR = {ISSUES[k]: c for k, c in PCOLOR.items()}           # same colours, keyed by label
TEALS = [SURFACE, "#10403a", "#14605a", "#1a8278", "#22a596"]   # sequential: near zero fades into the surface
SHORT = {"kyc_verification": "KYC", "rejection_no_reason": "No new loan", "hidden_charges": "Hidden charges",
         "disbursal_delay": "Disbursal delay", "customer_support": "Customer support", "app_bugs": "App bugs",
         "recovery_calls": "Recovery calls", "repayment_credit_score": "Repayment"}


def rgba(hex_colour, a):
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


pio.templates["loanvoice"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, size=13), colorway=SERIES,
    title=dict(font=dict(size=15, color=TEXT), x=0, xanchor="left", y=0.99, yanchor="top"),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, tickfont=dict(color=TEXT_2)),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER, tickfont=dict(color=TEXT_2)),
    legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(color=TEXT)),
    margin=dict(l=10, r=20, t=60, b=10),
))
px.defaults.template = "loanvoice"

st.markdown(f"""
<style>
.block-container {{padding-top: 2.2rem;}}
.lv-title {{font-size:2.1rem; font-weight:750; line-height:1.15; margin:.2rem 0 .3rem 0; color:{TEXT};}}
.lv-sub {{color:{TEXT_2}; font-size:1.05rem; margin-bottom:.8rem;}}
.lv-label {{color:{TEXT_2}; font-size:.95rem;}}
.lv-value {{font-family: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
            font-size:1.75rem; font-weight:600; color:{TEXT}; line-height:1.25; margin:.15rem 0 .1rem 0;}}
.lv-delta {{font-size:.88rem; color:{TEXT_2};}}
.lv-delta b {{font-weight:700;}}
.lv-card {{background:{SURFACE}; border:1px solid {BORDER}; border-top:4px solid var(--c); border-radius:12px;
          padding:16px 18px; min-height:330px;}}
.lv-card .rank {{font-size:.74rem; color:{TEXT_2}; text-transform:uppercase; letter-spacing:.08em;}}
.lv-card h4 {{margin:.25rem 0 .4rem 0; font-size:1.05rem; color:{TEXT};}}
.lv-card .big {{font-family:"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; font-size:1.6rem;
               font-weight:600; color:var(--c);}}
.lv-card .muted {{color:{TEXT_2}; font-size:.9rem;}}
.lv-card .fix {{margin-top:.7rem; font-size:.9rem; color:{TEXT}; border-top:1px solid {BORDER}; padding-top:.6rem;}}
.lv-note {{background:{SURFACE}; border:1px solid {BORDER}; border-left:4px solid {TEAL}; border-radius:12px;
          padding:14px 18px; color:{TEXT};}}
.lv-kicker {{text-transform:uppercase; letter-spacing:.09em; font-size:.72rem; color:{TEXT_2}; margin-bottom:.25rem;}}
.lv-month {{background:{SURFACE}; border:1px solid {BORDER}; border-top:4px solid var(--c); border-radius:12px;
           padding:16px 18px; min-height:360px;}}
.lv-month h4 {{margin:0 0 .6rem 0; color:{TEXT};}}
.lv-month li {{margin-bottom:.5rem; color:{TEXT}; font-size:.92rem;}}
.lv-tag {{display:inline-block; padding:1px 9px; border-radius:999px; font-size:.72rem; margin-left:6px;
         vertical-align:middle; color:{TEXT}; background:var(--bg); border:1px solid var(--c);}}
.lv-step {{background:{SURFACE}; border:1px solid {BORDER}; border-top:4px solid var(--c); border-radius:12px;
          padding:14px 16px; min-height:150px; color:{TEXT}; font-size:.9rem;}}
.lv-warn {{color:{TEXT_2}; font-size:.85rem;}}
</style>
""", unsafe_allow_html=True)

LOGO = (f'<svg xmlns="http://www.w3.org/2000/svg" width="190" height="34" viewBox="0 0 190 34">'
        f'<path d="M3 6a4 4 0 0 1 4-4h18a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H13l-6 6v-6H7a4 4 0 0 1-4-4z" fill="{TEAL}"/>'
        f'<rect x="9" y="14" width="3" height="5" rx="1" fill="{BG}"/><rect x="14.5" y="10" width="3" height="9" rx="1" fill="{BG}"/>'
        f'<rect x="20" y="7" width="3" height="12" rx="1" fill="{BG}"/>'
        f'<text x="38" y="16" font-family="sans-serif" font-size="15" font-weight="700" fill="{TEXT}">LoanVoice AI</text>'
        f'<text x="38" y="30" font-family="sans-serif" font-size="10.5" fill="{TEXT_2}">Review Intelligence</text></svg>')

# Share of keyword matches confirmed as real repeat customers in a manual check of 20 reviews (15 of 20).
KEYWORD_PRECISION = 0.75
REPEAT_RE = r"(?:paid|repay|closed|clear|foreclos|on time|again|next loan|new loan|another loan|second loan)"


# ---------------------------------------------------------------- data
@st.cache_data(show_spinner="Loading reviews from the database...")
def load_reviews():
    df = db.read_sql(db.get_engine(), "SELECT * FROM v_review_issues")
    df["review_date"] = pd.to_datetime(df["review_date"])
    df["issue_label"] = df.issue.map(ISSUES)
    df["month"] = df.review_date.dt.to_period("M")
    return df


@st.cache_data
def load_json(name):
    return json.loads((OUTPUT_DIR / name).read_text())


@st.cache_resource
def load_model():
    return joblib.load(OUTPUT_DIR / "issue_model.joblib")


@st.cache_resource
def get_search(_df):
    return ReviewSearch(_df)


try:
    reviews = load_reviews()
    metrics, stats, impact = load_json("model_metrics.json"), load_json("statistics.json"), load_json("impact.json")
except Exception as exc:
    st.error(f"Could not load data: {exc}\n\nRun `python pipeline.py run` first, and check DATABASE_URL.")
    st.stop()

APPS = sorted(reviews.app_name.unique())
APP_COLORS = {a: SERIES[i % len(SERIES)] for i, a in enumerate(APPS)}   # colour follows the app, never its rank
MONTHS = sorted(reviews.month.unique())
FIRST_DAY = reviews.groupby("app_name").review_date.min()
# First full month in which every app has data: before it, "all apps" mixes different sets of apps
COMMON_MONTH = (FIRST_DAY.max() + pd.offsets.MonthBegin(0) if FIRST_DAY.max().day > 1 else FIRST_DAY.max()).to_period("M")


# ---------------------------------------------------------------- building blocks
def plot(fig, where=None, height=None):
    """Show a Plotly chart with the house style."""
    has_legend = sum(1 for tr in fig.data if tr.showlegend is not False) > 1
    fig.update_layout(legend_title_text="", margin=dict(t=95 if has_legend else 55))
    if height:
        fig.update_layout(height=height)
    (where or st).plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def spark(values, colour=TEAL):
    """Small area chart for a KPI tile."""
    y = list(values)
    lo, hi = min(y), max(y)
    pad = (hi - lo) * 0.25 or abs(hi) * 0.05 or 1
    fig = go.Figure(go.Scatter(x=list(range(len(y))), y=y, mode="lines", line=dict(color=colour, width=2),
                               fill="tozeroy", fillcolor=rgba(colour, 0.22), hoverinfo="skip"))
    fig.update_layout(height=70, margin=dict(l=0, r=0, t=4, b=0), showlegend=False,
                      xaxis=dict(visible=False), yaxis=dict(visible=False, range=[lo - pad, hi + pad]))
    return fig


def tile(col, label, value, delta=None, delta_text="", note="", good_when_up=True, trend=None, colour=TEAL):
    """KPI tile: label, value, coloured change arrow and a sparkline."""
    with col.container(border=True):
        d = ""
        if delta is not None:
            arrow = "▲" if delta > 0 else "▼" if delta < 0 else "■"
            good = delta == 0 or (delta > 0) == good_when_up
            d = f'<div class="lv-delta"><b style="color:{GOOD if good else BAD}">{arrow} {delta_text}</b> {note}</div>'
        elif note:
            d = f'<div class="lv-delta">{note}</div>'
        st.markdown(f'<div class="lv-label">{label}</div><div class="lv-value">{value}</div>{d}', unsafe_allow_html=True)
        if trend is not None and len(trend) >= 3:
            st.plotly_chart(spark(trend, colour), width="stretch", config={"displayModeBar": False, "staticPlot": True})


def segmented(label, options, key):
    """Segmented buttons like QuickCart's region filter (radio buttons on older Streamlit)."""
    if hasattr(st, "segmented_control"):
        v = st.segmented_control(label, options, default=options[0], key=key, label_visibility="collapsed")
        return v or options[0]
    return st.radio(label, options, horizontal=True, key=key, label_visibility="collapsed")


def filter_bar(key, show_apps=True):
    """App buttons + From/To months + Reset. Returns (app, filtered reviews)."""
    c = st.columns([5.2, 1.4, 1.4, 0.7], vertical_alignment="bottom")
    with c[0]:
        app = segmented("App", ["All apps"] + APPS, f"{key}_app") if show_apps else "All apps"
    d = reviews if app == "All apps" else reviews[reviews.app_name == app]
    months = sorted(d.month.unique())
    start = COMMON_MONTH if app == "All apps" and COMMON_MONTH in months else months[0]
    fmt = lambda m: m.strftime("%b %Y")  # noqa: E731
    m_from = c[1].selectbox("From", months, index=months.index(start), format_func=fmt, key=f"{key}_from_{app}")
    m_to = c[2].selectbox("to", months, index=len(months) - 1, format_func=fmt, key=f"{key}_to_{app}")

    def reset():
        for k in [k for k in st.session_state if str(k).startswith(f"{key}_")]:
            del st.session_state[k]
    c[3].button("Reset", key=f"{key}_reset", on_click=reset, type="tertiary" if st.__version__ >= "1.41" else "secondary")
    if m_from > m_to:
        m_from, m_to = m_to, m_from
    d = d[(d.month >= m_from) & (d.month <= m_to)]
    if app == "All apps" and m_from < COMMON_MONTH:
        st.markdown(f'<div class="lv-warn">⚠ Before {COMMON_MONTH.strftime("%b %Y")} not all apps have data '
                    f'(download cap), so early months mix fewer apps.</div>', unsafe_allow_html=True)
    st.divider()
    return app, d


def monthly(d, fn, min_n=30):
    """Monthly values of fn(reviews of that month), skipping thin months."""
    return pd.Series({m: fn(g) for m, g in d.groupby("month") if len(g) >= min_n}).sort_index()


def weekly(d, fn, min_n=20):
    w = d.review_date.dt.to_period("W")
    s = pd.Series({k: fn(g) for k, g in d.groupby(w) if len(g) >= min_n}).sort_index()
    return s if len(s) >= 6 else monthly(d, fn, min_n=10)


def change(d, fn):
    """Last month vs first month in the selection: (delta, 'Nov vs Aug')."""
    m = monthly(d, fn)
    if len(m) < 2:
        return None, ""
    return m.iloc[-1] - m.iloc[0], f"{m.index[-1].strftime('%b')} vs {m.index[0].strftime('%b')}"


def issue_table(d):
    """Key numbers for every problem: size, severity, one-star reviews, agreement."""
    n_all, ones_all = len(d), int((d.rating == 1).sum())
    rows = []
    for k in PROBLEM_ISSUES:
        g = d[d.issue == k]
        if g.empty:
            continue
        rows.append({"issue": k, "label": ISSUES[k], "reviews": len(g), "per_1000": 1000 * len(g) / n_all,
                     "avg_rating": g.rating.mean(), "pct_one_star": (g.rating == 1).mean(),
                     "one_star": int((g.rating == 1).sum()),
                     "pct_of_all_one_star": (g.rating == 1).sum() / ones_all if ones_all else 0,
                     "votes_per_review": g.thumbs_up.mean()})
    return pd.DataFrame(rows).sort_values("one_star", ascending=False).reset_index(drop=True)


def header(title, sub):
    st.markdown(f'<div class="lv-title">{title}</div><div class="lv-sub">{sub}</div>', unsafe_allow_html=True)


def release_story(d):
    """The biggest significant rating drop after a release, and what happened to happy vs complaint reviews."""
    drops = [r for r in stats.get("release_tests", []) if r["significant"] and r["change"] < 0 and r["cohens_d"] <= -0.5]
    drops = [r for r in drops if r["app"] in set(d.app_name)]
    if not drops:
        return None
    r = min(drops, key=lambda x: x["cohens_d"])
    rel = pd.Timestamp(r["release_date"])
    g = reviews[reviews.app_name == r["app"]]
    before = g[(g.review_date < rel) & (g.review_date >= rel - pd.Timedelta(days=30))]
    after = g[(g.review_date >= rel) & (g.review_date < rel + pd.Timedelta(days=30))]
    count = lambda x: (int((x.issue == "positive").sum()), int(x.issue.isin(PROBLEM_ISSUES).sum()))  # noqa: E731
    (h0, c0), (h1, c1) = count(before), count(after)
    return {**r, "happy_before": h0, "happy_after": h1, "complaints_before": c0, "complaints_after": c1}


is_complaint = lambda g: g.issue.isin(PROBLEM_ISSUES).mean() * 100  # noqa: E731
one_star = lambda g: (g.rating == 1).mean() * 100                    # noqa: E731
avg_rating = lambda g: g.rating.mean()                               # noqa: E731


# ---------------------------------------------------------------- page 1: overview
def overview():
    t_all = issue_table(reviews)
    header("Review overview",
           f"{len(reviews):,} Google Play reviews from {len(APPS)} loan apps. "
           f"{html.escape(t_all.label[0])} is the biggest problem ({t_all.one_star[0]:,} one-star reviews).")
    app, d = filter_bar("ov")
    if d.empty:
        st.info("No reviews for this selection.")
        return
    t = issue_table(d)
    no_loan = lambda g: 1000 * (g.issue == "rejection_no_reason").mean()  # noqa: E731

    r1 = st.columns(2)
    dl, tx = change(d, avg_rating)
    tile(r1[0], "Average rating", f"{d.rating.mean():.2f} ★", dl, f"{dl:+.2f}" if dl is not None else "", tx,
         True, weekly(d, avg_rating))
    dl, tx = change(d, is_complaint)
    tile(r1[1], "Reviews naming a specific problem", f"{is_complaint(d):.1f}%", dl,
         f"{dl:+.1f} pts" if dl is not None else "", tx, False, weekly(d, is_complaint), colour=SERIES[1])
    r2 = st.columns(2)
    dl, tx = change(d, one_star)
    tile(r2[0], "One-star share", f"{one_star(d):.1f}%", dl, f"{dl:+.1f} pts" if dl is not None else "", tx,
         False, weekly(d, one_star), colour=SERIES[7])
    dl, tx = change(d, no_loan)
    tile(r2[1], '"No new loan" complaints per 1,000 reviews', f"{no_loan(d):.1f}", dl,
         f"{dl:+.1f}" if dl is not None else "", tx, False, weekly(d, no_loan), colour=PCOLOR["rejection_no_reason"])
    st.caption(f"▲▼ = last month vs first month of the selection. Green = better, red = worse. "
               f"AI labels are {metrics['accuracy']:.1%} accurate on {metrics['n_test']} hand-checked reviews.")

    if t.empty:
        return
    ones = int((d.rating == 1).sum())
    top3 = t.head(3)
    st.subheader(f"Three problems cause {top3.one_star.sum() / max(ones, 1):.0%} of all one-star reviews")
    angriest = t.loc[t.pct_one_star.idxmax(), "issue"]
    most_agreed = t.loc[t.votes_per_review.idxmax(), "issue"]
    cols = st.columns(3)
    for i, r in enumerate(top3.itertuples()):
        notes = []
        if r.issue == "rejection_no_reason":
            m = d[d.issue == r.issue].review_text.fillna("").str.contains(REPEAT_RE, case=False, regex=True).mean()
            notes.append(f"About {m * KEYWORD_PRECISION:.0%} are customers who say they already repaid "
                         f"({m:.0%} keyword matches × {KEYWORD_PRECISION:.0%} confirmed by hand).")
        if r.issue == angriest:
            notes.append(f"The angriest complaint: {r.pct_one_star:.0%} of these reviews are one-star.")
        if r.issue == most_agreed:
            notes.append(f"The complaint other users agree with most: {r.votes_per_review:.1f} helpful votes per review.")
        if r.issue == "recovery_calls":
            notes.append("Calling rules are also a regulatory (RBI) issue, not just a rating issue.")
        if not notes:
            notes.append(f"{r.pct_one_star:.0%} one-star, {r.votes_per_review:.1f} helpful votes per review.")
        cols[i].markdown(
            f'<div class="lv-card" style="--c:{PCOLOR[r.issue]}"><div class="rank">#{i + 1} by one-star reviews</div>'
            f'<h4>{html.escape(r.label)}</h4><div class="big">{r.one_star:,}</div>'
            f'<div class="muted">one-star reviews · {r.pct_of_all_one_star:.0%} of all</div>'
            f'<p class="muted" style="margin-top:.6rem">{" ".join(html.escape(x) for x in notes)}</p>'
            f'<div class="fix"><b>Fix:</b> {html.escape(PROPOSED_FIX[r.issue])}</div></div>', unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1, 1])
    tp = t.sort_values("one_star")
    fig = go.Figure(go.Bar(x=tp.one_star, y=tp.label, orientation="h", marker_color=[PCOLOR[k] for k in tp.issue],
                           marker_line=dict(color=BG, width=1), text=[f"{v:,}" for v in tp.one_star],
                           textposition="outside", textfont=dict(color=TEXT_2),
                           hovertemplate="%{y}<br>%{x:,} one-star reviews<extra></extra>"))
    fig.update_layout(title="One-star reviews by problem", xaxis_title=None, yaxis_title=None, showlegend=False)
    fig.update_xaxes(showgrid=False, showticklabels=False)
    plot(fig, left, height=400)

    comp = d[d.issue.isin(PROBLEM_ISSUES)]
    mix = comp.groupby(["month", "issue_label"]).size().reset_index(name="n")
    mix["share"] = mix.n / mix.groupby("month").n.transform("sum")
    mix = mix[mix.groupby("month").n.transform("sum") >= 30]
    mix["month"] = mix.month.dt.to_timestamp()
    order = [ISSUES[k] for k in t.issue]
    fig = px.bar(mix, x="month", y="share", color="issue_label", color_discrete_map=LCOLOR,
                 category_orders={"issue_label": order}, custom_data=["n"],
                 title="What people complain about, month by month (share of complaints)")
    fig.update_traces(marker_line=dict(color=BG, width=1),
                      hovertemplate="%{x|%b %Y}<br>%{y:.0%} of complaints (%{customdata[0]} reviews)<extra></extra>")
    fig.update_yaxes(tickformat=".0%", title=None)
    fig.update_xaxes(title=None, dtick="M1", tickformat="%b")
    plot(fig, right, height=400)

    s = release_story(d)
    if s:
        c0, c1, h0, h1 = s["complaints_before"], s["complaints_after"], s["happy_before"], s["happy_after"]
        happy_change = (h1 - h0) / h0 if h0 else 0
        comp_change = (c1 - c0) / c0 if c0 else 0
        why = "complaints barely moved" if abs(comp_change) < 0.2 else f"complaints changed {comp_change:+.0%}"
        a, b = st.columns([3, 2])
        a.markdown(
            f'<div class="lv-note" style="border-left-color:{SERIES[1]}"><div class="lv-kicker">Lesson from '
            f'{html.escape(s["app"])}</div><b>The rating fell {s["avg_before"]} → {s["avg_after"]}★ after version '
            f'{html.escape(str(s["version"]))}</b> (30 days before vs after {s["release_date"]}, Cohen\'s d = '
            f'{s["cohens_d"]}). But {why} ({c0} → {c1}) while happy reviews went {h0} → {h1} ({happy_change:+.0%}).'
            f'<br><br>Watch review volume next to the rating: a drop can mean happy users went quiet, '
            f'not that new problems appeared.</div>', unsafe_allow_html=True)
        bars = pd.DataFrame({"period": ["30 days before"] * 2 + ["30 days after"] * 2,
                             "type": ["Happy reviews", "Complaints"] * 2, "reviews": [h0, c0, h1, c1]})
        fig = px.bar(bars, x="type", y="reviews", color="period", barmode="group", text="reviews",
                     color_discrete_sequence=[TEAL, SERIES[1]])
        fig.update_traces(textposition="outside", textfont_color=TEXT_2, marker_line=dict(color=BG, width=1))
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        fig.update_yaxes(showgrid=False, showticklabels=False, range=[0, max(h0, h1, c0, c1, 1) * 1.25])
        plot(fig, b, height=260)

    st.markdown(f'<div class="lv-note"><div class="lv-kicker">Latest month (auto-generated)</div>'
                f'{monthly_brief(reviews, stats, impact).replace("**", "")}</div>', unsafe_allow_html=True)
    st.caption("Labels: hand-labelled where available, otherwise predicted by the AI model. Reviews come from a vocal "
               "minority of users, so they show what hurts most, not how many customers it affects.")


# ---------------------------------------------------------------- page 2: compare apps
def compare_apps():
    header("Compare apps", "Each app has a different main problem, so one roadmap does not fit all.")
    cols = st.columns(len(APPS))
    for i, a in enumerate(APPS):
        g = reviews[reviews.app_name == a]
        top = g[g.issue.isin(PROBLEM_ISSUES)].issue.value_counts()
        dl, tx = change(g, avg_rating)
        tile(cols[i], f'<b style="color:{APP_COLORS[a]}">●</b> {html.escape(a)}', f"{g.rating.mean():.2f} ★", dl,
             f"{dl:+.2f}" if dl is not None else "", tx, True, monthly(g, avg_rating, 10), colour=APP_COLORS[a])
        cols[i].markdown(f'<div class="lv-delta">{is_complaint(g):.1f}% complaints · main problem: '
                         f'<b style="color:{PCOLOR[top.index[0]] if len(top) else TEXT}">'
                         f'{html.escape(SHORT[top.index[0]]) if len(top) else "–"}</b><br>'
                         f'{len(g):,} reviews from {g.review_date.min():%d %b %Y}</div>', unsafe_allow_html=True)

    st.write("")
    prof = (reviews[reviews.issue.isin(PROBLEM_ISSUES)].groupby(["issue_label", "app_name"]).size()
            / reviews.groupby("app_name").size()).unstack().fillna(0)
    prof = prof.loc[prof.max(axis=1).sort_values().index]
    fig = px.imshow(prof * 100, text_auto=".1f", aspect="auto", color_continuous_scale=TEALS,
                    labels={"x": "", "y": "", "color": "%"}, title="Complaint profile: share of each app's own reviews (%)")
    fig.update_traces(textfont_color=TEXT)
    fig.update_layout(coloraxis_colorbar=dict(title=""))
    plot(fig, height=430)

    m = (reviews.groupby(["month", "app_name"]).rating.agg(["mean", "size"]).reset_index())
    m = m[m["size"] >= 30]
    m["month"] = m.month.dt.to_timestamp()
    fig = px.line(m, x="month", y="mean", color="app_name", markers=True, color_discrete_map=APP_COLORS,
                  labels={"mean": "Average rating", "month": "", "app_name": "App", "size": "Reviews"},
                  title="Average rating by month (months with 30+ reviews)", hover_data={"size": True})
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_xaxes(dtick="M1", tickformat="%b %Y")
    plot(fig, height=380)
    st.caption(f"Data starts on different dates per app (the big apps hit the 40,000-review download cap). "
               f"All apps have data from {FIRST_DAY.max():%d %b %Y}, so compare months from then on.")

    st.subheader("Each app's top 3 fixes (by expected rating gain)")
    rows = []
    for a, v in impact["by_app"].items():
        row = {"App": a}
        for i, t in enumerate(v["top_issues"], 1):
            row[f"Fix #{i}"] = f"{SHORT[t['issue']]} (+{t['gain']:.3f}★)"
        row["Rating today"] = v["current_avg"]
        row["If top 3 fixed"] = v["rating_if_top3_fixed"]
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("Expected gain assumes 60% of affected users are satisfied after a fix.")


# ---------------------------------------------------------------- page 3: issue explorer
def issue_explorer():
    header("Issue explorer", "One problem in depth: how big, how angry, which apps, and the reviews behind it.")
    app, d = filter_bar("ex")
    counts = d[d.issue.isin(PROBLEM_ISSUES)].issue.value_counts()
    order = list(counts.index) + [k for k in PROBLEM_ISSUES if k not in counts.index]   # biggest problem first
    issue = st.selectbox("Problem", order, format_func=lambda k: f"{ISSUES[k]} ({counts.get(k, 0):,} reviews)")
    g = d[d.issue == issue]
    if g.empty:
        st.info("No reviews about this problem for this selection.")
        return
    colour = PCOLOR[issue]
    share = lambda x: 1000 * (x.issue == issue).mean()  # noqa: E731
    c = st.columns(4)
    dl, tx = change(d, share)
    tile(c[0], "Reviews per 1,000", f"{share(d):.1f}", dl, f"{dl:+.1f}" if dl is not None else "", tx, False,
         weekly(d, share), colour=colour)
    tile(c[1], "One-star", f"{(g.rating == 1).mean():.0%}", note=f"average {g.rating.mean():.2f} ★ · {len(g):,} reviews")
    tile(c[2], "Helpful votes per review", f"{g.thumbs_up.mean():.1f}", note="how much other users agree")
    if issue == "rejection_no_reason":
        m = g.review_text.fillna("").str.contains(REPEAT_RE, case=False, regex=True).mean()
        tile(c[3], "Say they already repaid", f"~{m * KEYWORD_PRECISION:.0%}", note="keyword match × manual check")
    else:
        tile(c[3], "Effort to fix", f"{EFFORT_POINTS[issue]}/5", note="analyst estimate")

    st.markdown(f'<div class="lv-note" style="border-left-color:{colour}"><b>Proposed fix:</b> '
                f'{html.escape(PROPOSED_FIX[issue])}</div>', unsafe_allow_html=True)
    tr = (d.groupby(["month", "app_name"]).agg(share=("issue", lambda s: (s == issue).mean()), n=("issue", "size"))
          .reset_index())
    tr = tr[tr.n >= 30]
    tr["month"] = tr.month.dt.to_timestamp()
    fig = px.line(tr, x="month", y="share", color="app_name", markers=True, color_discrete_map=APP_COLORS,
                  labels={"share": "Share of reviews", "month": "", "app_name": "App", "n": "Reviews that month"},
                  title=f"{ISSUES[issue]}: share of each app's reviews by month", hover_data={"n": True})
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_yaxes(tickformat=".1%")
    fig.update_xaxes(dtick="M1", tickformat="%b %Y")
    plot(fig, height=360)

    st.subheader("Reviews behind it (most helpful first)")
    show = g.sort_values(["thumbs_up", "review_date"], ascending=False).head(30)
    st.dataframe(show[["review_date", "app_name", "rating", "thumbs_up", "review_text", "label_source", "confidence"]]
                 .rename(columns={"review_date": "date", "app_name": "app", "thumbs_up": "helpful votes",
                                  "review_text": "review", "label_source": "label from"}),
                 width="stretch", hide_index=True,
                 column_config={"date": st.column_config.DateColumn(format="DD MMM YYYY")})


# ---------------------------------------------------------------- page 4: simulator
def simulator():
    header("What if we fix it?", "Pick the problems to fix and how many affected users a fix would satisfy. "
                                 "See the one-star reviews prevented and the rating gain.")
    app, d = filter_bar("sim")
    if d.empty:
        st.info("No reviews for this selection.")
        return
    gains = rating_gain_table(d, DEFAULT_FIX_RATE)
    c = st.columns([2, 1])
    chosen = c[0].multiselect("Problems to fix", list(gains.issue), default=list(gains.issue[:3]),
                              format_func=lambda k: ISSUES[k])
    fix_rate = c[1].slider("Affected users satisfied after the fix (assumption)", 0.2, 1.0, DEFAULT_FIX_RATE, 0.05)
    if not chosen:
        st.info("Choose at least one problem.")
        return
    t = issue_table(d).set_index("issue")
    n = len(d)
    ones_sel = int(t.loc[chosen, "one_star"].sum())
    prevented = fix_rate * ones_sel
    g = rating_gain_table(d, fix_rate).set_index("issue")
    current = d.rating.mean()
    projected = current + g.loc[chosen, "expected_rating_gain"].sum()

    k = st.columns(4)
    tile(k[0], "One-star reviews prevented", f"{prevented:,.0f}", prevented, f"{prevented / max(ones_sel, 1):.0%}",
         f"of {ones_sel:,} from these problems", True)
    tile(k[1], "One-star from these problems, per 1,000", f"{1000 * (ones_sel - prevented) / n:.1f}",
         -1000 * prevented / n, f"{-1000 * prevented / n:.1f}", f"from {1000 * ones_sel / n:.1f} today", False)
    tile(k[2], f"Average rating ({app})", f"{projected:.2f} ★", projected - current, f"{projected - current:+.2f}",
         f"from {current:.2f} today", True)
    tile(k[3], "Total effort", f"{sum(EFFORT_POINTS[i] for i in chosen)} pts", note="1–5 per problem (analyst estimate)")

    st.write("")
    left, right = st.columns([3, 2])
    fig = go.Figure()
    labels = [ISSUES[i] for i in chosen]
    fig.add_bar(y=labels, x=[t.loc[i, "one_star"] for i in chosen], orientation="h", name="Today", marker_color=MUTED,
                text=[f"{t.loc[i, 'one_star']:,}" for i in chosen], textposition="outside", textfont_color=TEXT_2)
    fig.add_bar(y=labels, x=[t.loc[i, "one_star"] * (1 - fix_rate) for i in chosen], orientation="h",
                name="After the fix", marker_color=[PCOLOR[i] for i in chosen],
                text=[f"{t.loc[i, 'one_star'] * (1 - fix_rate):,.0f}" for i in chosen], textposition="outside",
                textfont_color=TEXT_2)
    fig.update_layout(barmode="group", title="One-star reviews: today (grey) vs after the fix (colour)",
                      yaxis=dict(autorange="reversed"), showlegend=False)
    fig.update_xaxes(showgrid=False, showticklabels=False)
    plot(fig, left, height=150 + 80 * len(chosen))
    with right:
        st.markdown("**How sure is this?** The fix rate is an assumption, so here is the result at three values:")
        sens = []
        for fr in (0.4, 0.6, 0.8):
            gg = rating_gain_table(d, fr).set_index("issue")
            sens.append({"Fix rate": f"{fr:.0%}", "One-star reviews prevented": f"{fr * ones_sel:,.0f}",
                         "Average rating": f"{current + gg.loc[chosen, 'expected_rating_gain'].sum():.2f} ★"})
        st.dataframe(pd.DataFrame(sens), width="stretch", hide_index=True)
        st.caption("Rating gain = share of reviews × fix rate × (average rating without the problem − with it). "
                   "One-star reviews prevented = one-star reviews from the chosen problems × fix rate. "
                   "A same-period comparison; it does not predict future review volume.")


# ---------------------------------------------------------------- page 5: roadmap
ROADMAP = {
    ("Month 1 · quick wins + compliance", TEAL): [
        ("rejection_no_reason", "Decline reason + reapply date screen; warning before foreclosure"),
        ("app_bugs", "Crash monitoring, staged rollouts, 48-hour hotfix rule"),
        ("recovery_calls", "Written calling rules for all agencies: 8:00–19:00 only, max 3 calls a day, no calls to contacts"),
    ],
    ("Month 2 · medium projects", SERIES[0]): [
        ("repayment_credit_score", "'Pay now' before auto-debit; retry auto-debit before any late fee; no fee on a logged outage"),
        ("recovery_calls", "Calling limits enforced in the system + 'report a recovery call' button"),
        ("hidden_charges", "One 'total cost' screen before e-sign"),
    ],
    ("Month 3 · bigger projects + measure", SERIES[6]): [
        ("customer_support", "In-app ticket tracking and callback booking"),
        ("disbursal_delay", "Live disbursal tracker (speeding up partner banks is a later project)"),
        (None, "Re-run this analysis on new reviews and check every KPI against its target"),
        ("kyc_verification", "Deferred: low volume and high effort"),
    ],
}


def roadmap():
    header("Roadmap", "Ranked by expected rating gain ÷ effort, with one deliberate exception: recovery-call rules move "
                      "up because they are a regulatory risk.")
    cols = st.columns(3)
    for col, ((month, colour), items) in zip(cols, ROADMAP.items()):
        lis = "".join(f"<li>{html.escape(text)}" + (f'<span class="lv-tag" style="--c:{PCOLOR[k]};--bg:{rgba(PCOLOR[k], 0.25)}">'
                                                     f'{html.escape(SHORT[k])}</span>' if k else "") + "</li>"
                      for k, text in items)
        col.markdown(f'<div class="lv-month" style="--c:{colour}"><h4>{html.escape(month)}</h4><ul>{lis}</ul></div>',
                     unsafe_allow_html=True)

    st.write("")
    st.subheader("Priority ranking (all apps)")
    fix_rate = st.slider("Affected users satisfied after a fix (assumption)", 0.2, 1.0, DEFAULT_FIX_RATE, 0.05,
                         key="roadmap_fix_rate")
    g = rating_gain_table(reviews, fix_rate)
    fig = go.Figure(go.Bar(x=g.priority_score, y=g.label, orientation="h", marker_color=[PCOLOR[k] for k in g.issue],
                           marker_line=dict(color=BG, width=1),
                           customdata=list(zip(g.expected_rating_gain.round(3), g.effort_points)),
                           hovertemplate="%{y}<br>gain +%{customdata[0]}★ ÷ effort %{customdata[1]}<extra></extra>"))
    fig.update_layout(title="Priority score = expected rating gain ÷ effort", yaxis=dict(autorange="reversed"),
                      showlegend=False)
    fig.update_xaxes(title=None)
    plot(fig, height=380)
    show = pd.DataFrame({"Rank": g.priority_rank, "Problem": g.label, "Reviews": g.n_reviews,
                         "Avg ★ with": g.avg_rating_with.round(2), "Expected gain (★)": g.expected_rating_gain.round(3),
                         "Effort (1–5)": g.effort_points, "Proposed fix": g.issue.map(PROPOSED_FIX)})
    st.dataframe(show, width="stretch", hide_index=True)
    st.caption("Effort points are analyst estimates to agree with the engineering lead (see docs/business_analysis.md).")


# ---------------------------------------------------------------- page 6: how it works
def how_it_works():
    header("How it works", "Where the data comes from, how reviews are labelled, how good the labels are, and what the "
                           "statistics can and cannot say.")
    steps = [("1. Collect", "Google Play reviews of 4 Indian loan apps (google-play-scraper), reviewer names dropped"),
             ("2. Store", "PostgreSQL tables + a view with one row per review and its final label"),
             ("3. Label", "Hand labels (2,000) + a rule for 1–2 word reviews + the AI model for the rest"),
             ("4. Test", "Chi-square, Wilson confidence intervals, Welch t-tests on releases (Bonferroni)"),
             ("5. Decide", "Rating gain ÷ effort → roadmap, KPIs and a recommendation memo")]
    for col, (h, s), colour in zip(st.columns(5), steps, [TEAL, SERIES[0], SERIES[6], SERIES[3], SERIES[1]]):
        col.markdown(f'<div class="lv-step" style="--c:{colour}"><b>{h}</b><br>{s}</div>', unsafe_allow_html=True)

    st.subheader("Data coverage")
    cov = reviews.groupby("app_name").agg(reviews=("review_id", "size"), first_review=("review_date", "min"),
                                         last_review=("review_date", "max"), avg_rating=("rating", "mean")).reset_index()
    cov["avg_rating"] = cov.avg_rating.round(2)
    st.dataframe(cov, width="stretch", hide_index=True,
                 column_config={"first_review": st.column_config.DateColumn(format="DD MMM YYYY"),
                                "last_review": st.column_config.DateColumn(format="DD MMM YYYY")})

    st.subheader("AI labelling model")
    c = st.columns(3)
    tile(c[0], "Accuracy on unseen reviews", f"{metrics['accuracy']:.1%}", 0.042, "+4.2 pts", "vs text-only model (87.6%)")
    tile(c[1], "Macro F1", f"{metrics['macro_f1']:.3f}", note="every problem counts equally")
    tile(c[2], "Hand-labelled reviews", f"{metrics['n_train']:,} · {metrics['n_test']:,}", note="training · test")
    st.caption("Model: TF-IDF on words and character pieces + the star rating → logistic regression. Error analysis "
               "showed the text-only model calling happy 5-star reviews that mention 'loan' a complaint.")
    labels = [ISSUES[k] for k in metrics["labels"]]
    cm = pd.DataFrame(metrics["confusion_matrix"], index=labels, columns=labels)
    fig = px.imshow(cm, text_auto=True, aspect="auto", color_continuous_scale=TEALS,
                    labels={"x": "Predicted by the model", "y": "Hand label", "color": "Reviews"},
                    title="Confusion matrix (500 test reviews)")
    fig.update_traces(textfont_color=TEXT)
    plot(fig, height=520)
    per = pd.DataFrame(metrics["per_class"]).T.rename(index=ISSUES)
    st.dataframe(per, width="stretch")
    with st.expander("Where the model goes wrong (examples)"):
        st.dataframe(pd.DataFrame(metrics["example_mistakes"]), width="stretch", hide_index=True)
    st.markdown("**Try the model**")
    tc = st.columns([3, 1])
    text = tc[0].text_input("Type a review", "Loan approved 5 days ago but money still not credited")
    stars = tc[1].select_slider("Star rating", options=[1, 2, 3, 4, 5], value=1)
    if text:
        model = load_model()
        proba = pd.Series(model.predict_proba(pd.DataFrame({"review_text": [text], "rating": [stars]}))[0],
                          index=model.classes_).sort_values(ascending=False)
        k = proba.index[0]
        st.markdown(f'Predicted problem: <b style="color:{PCOLOR.get(k, TEXT)}">{html.escape(ISSUES[k])}</b> '
                    f'({proba.iloc[0]:.0%} confidence)', unsafe_allow_html=True)

    st.subheader("Statistics")
    chi = stats["chi_square"]
    st.markdown(f"**Chi-square, problem vs rating group:** χ² = {chi['chi2']:,}, df = {chi['dof']}, p {chi['p_text']}, "
                f"Cramér's V = {chi['cramers_v']}.")
    st.caption("Caution: partly circular. Short reviews are labelled from their stars and the model also uses the stars, "
               "so this describes the data. The earlier text-only model gave the same severity order.")
    ci = pd.DataFrame(stats["one_star_by_issue"]).sort_values("one_star_share")
    fig = go.Figure()
    for r in ci.itertuples():
        colour = PCOLOR.get(r.issue, TEXT_2)
        fig.add_scatter(x=[r.one_star_share], y=[r.label], mode="markers", marker=dict(size=12, color=colour),
                        error_x=dict(type="data", symmetric=False, array=[r.ci_high - r.one_star_share],
                                     arrayminus=[r.one_star_share - r.ci_low], color=colour, thickness=2),
                        hovertemplate=f"{r.label}<br>{r.one_star_share:.0%} one-star (95% CI {r.ci_low:.0%}–{r.ci_high:.0%})"
                                      "<extra></extra>")
    fig.update_layout(title="Share of one-star reviews by problem (95% Wilson confidence interval)", showlegend=False)
    fig.update_xaxes(tickformat=".0%")
    plot(fig, height=420)
    st.markdown("**Did a release change the rating?** (30 days before vs after each new version)")
    rel = pd.DataFrame(stats["release_tests"], columns=["app", "version", "release_date", "avg_before", "avg_after",
                                                        "change", "cohens_d", "p_text", "significant"])
    st.dataframe(rel, width="stretch", hide_index=True)
    st.caption(f"Welch's t-test; significant = p below {stats['bonferroni_alpha']} (Bonferroni). "
               "Judge size by Cohen's d: with thousands of reviews even tiny changes are 'significant'.")

    st.subheader("Limits")
    st.markdown("- Reviews come from a vocal minority: they show what hurts, not how many customers it affects.\n"
                "- Each big app was capped at its newest 40,000 reviews, so apps cover different date ranges.\n"
                "- Labels are AI-assisted; small problems have few test reviews, so their scores are uncertain.\n"
                "- A first review of a version is not its release date; only versions newer than all earlier ones count.\n"
                "- 140 copied reviews (0.1%) are kept and reported, not deleted.")


# ---------------------------------------------------------------- page 7: ask the reviews
def ask_reviews():
    header("Ask the reviews", "Ask in plain English. The app finds the most related reviews and summarises them.")
    app = segmented("App", ["All apps"] + APPS, "ask_app")
    q = st.text_input("Question", "Why are users angry about money not being credited?")
    if q:
        hits = get_search(reviews).search(q, k=25, app=None if app == "All apps" else app)
        answer = llm_answer(q, hits) if len(hits) else None
        if answer and not answer.startswith("(LLM unavailable"):
            st.markdown(f'<div class="lv-note">{html.escape(answer)}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="lv-note">{data_summary(q, hits).replace("**", "")}</div>', unsafe_allow_html=True)
            if answer:
                st.caption(answer)
        st.write("")
        st.dataframe(hits[["review_date", "app_name", "rating", "issue_label", "review_text"]].head(15)
                     .rename(columns={"review_date": "date", "app_name": "app", "issue_label": "problem",
                                      "review_text": "review"}),
                     width="stretch", hide_index=True,
                     column_config={"date": st.column_config.DateColumn(format="DD MMM YYYY")})
    st.caption("Search uses TF-IDF. Set OLLAMA_MODEL, or LLM_BASE_URL / LLM_API_KEY / LLM_MODEL, to have an LLM "
               "write the answer.")


# ---------------------------------------------------------------- navigation (tabs at the top)
try:
    st.logo(LOGO, size="large")
except Exception:   # very old Streamlit: show the name as text
    st.sidebar.markdown("### LoanVoice AI")
pages = [
    st.Page(overview, title="Overview", icon=":material/bar_chart:", default=True),
    st.Page(compare_apps, title="Compare apps", icon=":material/compare_arrows:"),
    st.Page(issue_explorer, title="Issue explorer", icon=":material/manage_search:"),
    st.Page(simulator, title="What if we fix it?", icon=":material/tune:"),
    st.Page(roadmap, title="Roadmap", icon=":material/route:"),
    st.Page(how_it_works, title="How it works", icon=":material/science:"),
    st.Page(ask_reviews, title="Ask the reviews", icon=":material/forum:"),
]
try:
    page = st.navigation(pages, position="top")
except TypeError:   # Streamlit older than 1.46: tabs in the sidebar instead
    page = st.navigation(pages)
page.run()
