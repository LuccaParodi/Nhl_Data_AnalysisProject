# 🏒 2010s NHL: Can You Predict a Stanley Cup Champion?

An 11-season analysis of NHL team performance data (2008–2019), built to audit a viral claim: that special teams, goaltending, and finishing rate reliably predict Stanley Cup champions.

Spoiler: *kind of, but it's complicated.*

---

## The Question

A tweet claimed that the last 10 Stanley Cup winners shared five measurable traits — top-12 in PP%, PK%, xGF%, xGA%, and 5v5 SV%. The implication: championships are predictable. I pulled 11 seasons of NHL data to find out if that holds up.

## The Data

- **Source:** NHL API via [`nhl-api-py`](https://github.com/coreyjs/nhl-api-py)
- **Scope:** All 30 (then 31 with the addition of Las Vegas to the league) teams, 2008–2019, regular season + playoffs
- **Storage:** SQLite (`nhl_master.db`) — one row per team, per season, per stage
- **Metrics:** PK%, PP%, xG%, xG/G, GSAx, Finishing Rate, Net xG/G

## Structure

```
📓 2010sNHL.ipynb
├── Hypothesis          # Small introduction, The tweet, the question, context
├── Season-by-Season    # Per-season breakdown, 2008–2019 (collapsible)
└── All-Season Analysis # Cross-season master table, champion profile, correlation heatmap, rank plots
└── Conclusions         # Self-Explainatory
```

## Key Findings

- **GSAx (0.27)** is the strongest correlator with championship outcome — goaltending is the closest thing to a differentiator
- **PK% (0.09) and PP% (0.03)** show negligible correlation — the original hypothesis doesn't hold
- Champions are almost always elite across all metrics, but so are teams eliminated in round 2
- **The actual finding:** these metrics define the field of contention, not the winner. Being elite is necessary, not sufficient.
- The dynasty exception (Chicago 3x in 5 years, Pittsburgh back-to-back, LA's 2 cups in 3 years) suggests sustained organizational excellence matters more than any single-season metric

## Stack

```
Python · pandas · SQLite · nhl-api-py · matplotlib · seaborn · plotly · Google Colab
```

## Why 2008–2019?

NHL 2K10 is a banger of a videogame and my first contact with hockey as a kid on my ps2. Also: Crosby's three Cups, Ovi finally getting his, Kane's dynasty run with Chicago — it's the most interesting window of modern NHL history for this kind of analysis.
