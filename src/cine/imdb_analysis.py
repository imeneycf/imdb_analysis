import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt

    return alt, mo, pl


@app.cell
def _(mo):
    def kpi(label, value):
        return mo.Html(
            f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div></div>'
        )

    mo.Html("""
    <div class="hide-cell"></div>
    <style>
    @import url("https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css");
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap");

    /* Masque cette cellule en app view uniquement (reste visible et éditable en mode édition) */
    .marimo-cell:not(.interactive):has(.hide-cell),
    .marimo-cell:not(.interactive):empty { display: none; }

    :root {
      --marimo-text-font: 'Inter', system-ui, -apple-system, sans-serif;
      --marimo-heading-font: 'Inter', system-ui, -apple-system, sans-serif;
      --marimo-monospace-font: 'JetBrains Mono', ui-monospace, monospace;
    }
    h1, h2, h3 { font-weight: 600; letter-spacing: -0.02em; }
    h1 { font-size: 1.9rem; margin: 0.5rem 0 0.25rem; }
    h2 { font-size: 1.2rem; margin-top: 2.2rem; padding-bottom: 0.5rem;
         border-bottom: 1px solid var(--border); }
    h1 i, h2 i { color: var(--primary); margin-right: 0.35rem; }

    .kpi { background: var(--card); border: 1px solid var(--border); border-radius: 12px;
           padding: 14px 18px; min-width: 150px; }
    .kpi-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em;
                 color: var(--muted-foreground); font-weight: 500; }
    .kpi-value { font-size: 1.7rem; font-weight: 600; letter-spacing: -0.02em; margin-top: 2px; }
    </style>
    """)
    return (kpi,)


@app.cell
def _(mo):
    _dark = mo.app_meta().theme == "dark"
    pal = (
        dict(text="#eceeed", muted="#aab2af", border="#3b403e", alpha=0.6,
             cat=["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"])
        if _dark else
        dict(text="#0f172a", muted="#64748b", border="#e2e8f0", alpha=0.35,
             cat=["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"])
    )

    def themed(chart):
        font = "Inter, system-ui, sans-serif"
        return chart.configure(
            background="transparent",
            view=dict(stroke=None),
            axis=dict(gridColor=pal["border"], domainColor=pal["border"], tickColor=pal["border"],
                      labelColor=pal["muted"], titleColor=pal["muted"], labelFont=font, titleFont=font,
                      labelFontSize=11, titleFontSize=11, titleFontWeight=500),
            legend=dict(labelColor=pal["text"], titleColor=pal["muted"], labelFont=font, titleFont=font,
                        labelFontSize=11, titleFontSize=11, titleFontWeight=500, symbolType="circle"),
            range=dict(category=pal["cat"]),
            mark=dict(color=pal["cat"][0]),
            title=dict(color=pal["text"], font=font),
        )

    return pal, themed


@app.cell
def _(mo):
    mo.md("""
    #<i class="ri-clapperboard-fill"></i> Analysis of IMDb movies and series
    Exploration of several hundred thousand titles: genres, runtimes, decades, top-rated series,
    plus a mini recommendation explorer.
    """)
    return


@app.cell
def _(pl):
    _basics = pl.scan_csv(
        "data/title.basics.tsv",
        separator="\t",
        null_values="\\N",
        quote_char=None,
        infer_schema=False,
    )
    _ratings = pl.scan_csv(
        "data/title.ratings.tsv",
        separator="\t",
        null_values="\\N",
        quote_char=None,
    )

    titles = (
        _basics
        .filter(pl.col("titleType").is_in(["movie", "tvSeries", "tvMiniSeries"]))
        .join(_ratings, on="tconst", how="inner")
        .with_columns(
            pl.col("startYear").cast(pl.Int32, strict=False),
            pl.col("endYear").cast(pl.Int32, strict=False),
            pl.col("runtimeMinutes").cast(pl.Int32, strict=False),
            pl.col("isAdult").cast(pl.Int8, strict=False),
            pl.col("genres").str.split(","),
        )
        .filter((pl.col("isAdult") == 0) & (pl.col("numVotes") >= 100))
        .select(
            "tconst", "titleType", "primaryTitle", "startYear", "endYear",
            "runtimeMinutes", "genres", "averageRating", "numVotes",
        )
        .collect()
    )
    titles
    return (titles,)


@app.cell
def _(kpi, mo, pl, titles):
    mo.hstack([
        kpi("Titles", f"{titles.height:,}".replace(",", " ")),
        kpi("Movies", f"{titles.filter(pl.col('titleType') == 'movie').height:,}".replace(",", " ")),
        kpi("Series", f"{titles.filter(pl.col('titleType') != 'movie').height:,}".replace(",", " ")),
        kpi("Average rating", f"{titles['averageRating'].mean():.2f}"),
    ], widths="equal", gap=1)
    return


@app.cell
def _(titles):
    genres_df = (
        titles
        .explode("genres")
        .rename({"genres": "genre"})
        .drop_nulls("genre")
    )
    genres_df.head()
    return (genres_df,)


@app.cell
def _(mo):
    min_votes_genre = mo.ui.slider(1_000, 200_000, step=1_000, value=25_000, label="Votes minimum", show_value=True)
    min_votes_genre
    return (min_votes_genre,)


@app.cell
def _(genres_df, min_votes_genre, mo, pl):
    # Extract the highest-rated movies from each genre

    best_by_genre = (
        genres_df
        .filter(
            (pl.col("titleType") == "movie")
            & (pl.col("numVotes") >= min_votes_genre.value)
        )
        .sort(["averageRating", "numVotes"], descending=True)
        .group_by("genre", maintain_order=True)
        .first()
        .select("genre", "primaryTitle", "startYear", "averageRating", "numVotes")
        .sort("genre")
    )
    mo.vstack([
        mo.md("## <i class='ri-trophy-line'></i> Best movie by genre"),
        best_by_genre,
    ])
    return


@app.cell
def _(pl, titles):
    movies = titles.filter(
        (pl.col("titleType") == "movie")
        & pl.col("runtimeMinutes").is_between(40, 240)
    )
    runtime_corr = movies.select(pl.corr("runtimeMinutes", "averageRating")).item()

    by_runtime = (
        movies
        .with_columns(tranche_min=(pl.col("runtimeMinutes") // 15) * 15)
        .group_by("tranche_min")
        .agg(
            n=pl.len(),
            average_rating=pl.col("averageRating").mean(),
            median_rating=pl.col("averageRating").median(),
        )
        .sort("tranche_min")
    )
    by_runtime
    return by_runtime, movies, runtime_corr


@app.cell
def _(alt, by_runtime, mo, movies, pal, pl, runtime_corr, themed):
    # Correlation between film length and ratings

    _sample = movies.filter(pl.col("numVotes") >= 5_000)
    _sample = _sample.sample(min(3_000, _sample.height), seed=42)

    _points = alt.Chart(_sample).mark_circle(opacity=pal["alpha"], size=20).encode(
        x=alt.X("runtimeMinutes:Q", title="Length (min)"),
        y=alt.Y("averageRating:Q", title="IMDb rating", scale=alt.Scale(domain=[1, 10])),
        tooltip=["primaryTitle", "startYear", "runtimeMinutes", "averageRating"],
    )
    _line = alt.Chart(by_runtime).mark_line(color=pal["cat"][1], strokeWidth=3).encode(
        x="tranche_min:Q",
        y="average_rating:Q",
    )

    mo.vstack([
        mo.md(f"## <i class='ri-hourglass-2-fill'></i> Length vs rating — Pearson correlation : **{runtime_corr:.3f}**"),
        mo.ui.altair_chart(themed(_points + _line)),
    ])
    return


@app.cell
def _(pl, titles):
    # Sort by decade

    by_decade = (
        titles
        .filter(pl.col("startYear").is_between(1920, 2029))
        .with_columns(decade=(pl.col("startYear") // 10) * 10)
        .group_by("decade", "titleType")
        .agg(
            n=pl.len(),
            average_rating=pl.col("averageRating").mean(),
            median_rating=pl.col("averageRating").median(),
            median_length=pl.col("runtimeMinutes").median(),
        )
        .sort("decade")
    )
    by_decade
    return (by_decade,)


@app.cell
def _(alt, by_decade, mo, themed):
    _notes = alt.Chart(by_decade).mark_line(point=True).encode(
        x=alt.X("decade:O", title="Decade"),
        y=alt.Y("average_rating:Q", title="Average rating", scale=alt.Scale(zero=False)),
        color="titleType:N",
    )
    _volume = alt.Chart(by_decade).mark_bar().encode(
        x=alt.X("decade:O", title="Decade"),
        y=alt.Y("n:Q", title="Number of titles"),
        color="titleType:N",
    )
    mo.vstack([
        mo.md("## <i class='ri-calendar-2-line'></i> Trends by decade"),
        mo.hstack([themed(_notes), themed(_volume)]),
    ])
    return


@app.cell
def _(alt, genres_df, pl, themed):
    genre_trend = (
        genres_df
        .filter((pl.col("titleType") == "movie") & pl.col("startYear").is_between(1950, 2029))
        .with_columns(decade=(pl.col("startYear") // 10) * 10)
        .group_by("decade", "genre")
        .agg(n=pl.len())
        .with_columns(part=pl.col("n") / pl.col("n").sum().over("decade"))
    )
    themed(
        alt.Chart(genre_trend).mark_area().encode(
            x="decade:O",
            y=alt.Y("part:Q", stack="normalize", title="Share of genre tags"),
            color="genre:N",
            tooltip=["genre", "decade", alt.Tooltip("part:Q", format=".1%")],
        )
    )
    return


@app.cell(hide_code=True)
def _(mo, pl, titles):
    series = titles.filter(pl.col("titleType").is_in(["tvSeries", "tvMiniSeries"]))
    _m = 10_000
    _C = series["averageRating"].mean()

    top_series = (
        series
        .filter(pl.col("numVotes") >= _m)
        .with_columns(
            score=(pl.col("numVotes") / (pl.col("numVotes") + _m)) * pl.col("averageRating")
            + (_m / (pl.col("numVotes") + _m)) * _C
        )
        .sort("score", descending=True)
        .head(25)
        .with_columns(pl.col("genres").list.join(", "), pl.col("score").round(2))
        .select("primaryTitle", "startYear", "endYear", "genres", "averageRating", "numVotes", "score")
    )
    mo.vstack([mo.md("## <i class='ri-tv-2-line'></i> Top 25 series (weighted rating)"), top_series])
    return (series,)


@app.cell
def _(mo, pl, series):
    _by_rating = series.filter(pl.col("numVotes") >= 1_000).sort("averageRating", descending=True).head(10).select("primaryTitle", "averageRating", "numVotes")
    _by_votes = series.sort("numVotes", descending=True).head(10).select("primaryTitle", "averageRating", "numVotes")
    mo.hstack([
        mo.vstack([mo.md("**Raw top rating**"), _by_rating]),
        mo.vstack([mo.md("**Top number of votes**"), _by_votes]),
    ])
    return


if __name__ == "__main__":
    app.run()
