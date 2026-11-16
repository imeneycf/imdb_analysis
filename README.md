# IMDb Movies & Series Analysis
 
An interactive [marimo](https://marimo.io) notebook that explores several hundred thousand IMDb titles: genres, runtimes, decades, top-rated series, and a random-pick tool to find something to watch. Built with [Polars](https://pola.rs) for the data work and [Altair](https://altair-viz.github.io) for the charts.

## What's inside
 
| Section | What it shows |
|---|---|
| **Overview** | KPI cards (titles, movies, series, average rating) and a preview of the cleaned dataset. |
| **Best movie by genre** | Highest-rated movie in each genre, with an adjustable minimum-votes slider so obscure titles don't win on a handful of ratings. |
| **Length vs rating** | Scatter plot of runtime against IMDb rating (sample of well-rated-and-voted movies), the Pearson correlation, and a trend line of the mean rating per 15-minute runtime bucket. |
| **Trends by decade** | Average rating and number of titles per decade, split by title type (movie, series, mini-series). |
| **Genre mix over time** | Share of each genre among movies, decade by decade (normalized stacked area chart). |
| **Top 25 series** | Series ranked with a weighted (Bayesian) rating, next to the raw top by rating and the top by number of votes. |
| **Random pick** | Filter by type, genre, years, runtime, minimum rating and votes, then draw a random title. The result is placed in context: its rating percentile, the size of the filtered pool, and the rating distribution of that pool. |

## Data
 
The notebook uses the [IMDb non-commercial datasets](https://developer.imdb.com/non-commercial-datasets/) (download page: <https://datasets.imdbws.com/>). Two files are needed:
 
- `title.basics.tsv` (title type, name, years, runtime, genres)
- `title.ratings.tsv` (average rating and number of votes)
Unzip them into a `data/` folder next to the notebook:
 
```
.
├── imdb_analysis.py        # the marimo notebook (rename to match your file)
├── data/
│   ├── title.basics.tsv
│   └── title.ratings.tsv
└── README.md
```
 
> The IMDb datasets are provided for personal, non-commercial use. Do not commit them to a public repository; add `data/` to your `.gitignore`.

### Cleaning and filtering
 
- Keep only `movie`, `tvSeries` and `tvMiniSeries` titles.
- Drop adult titles.
- Keep titles with at least **100 votes**, so ratings are not meaningless.
- Parse years and runtimes as integers (invalid values become nulls) and split `genres` into a list.
- Data is loaded lazily (`scan_csv`) and collected once, which keeps loading fast even on the full dataset.


## Methodology notes
 
- **Weighted rating (top series).** To avoid a 10/10 with 200 votes beating a 9/10 with 500,000 votes, series are ranked with the classic Bayesian average:
  `score = v / (v + m) · R + m / (v + m) · C`
  where `R` is the title's rating, `v` its number of votes, `m` the vote threshold (10,000) and `C` the mean rating across all series. Only series with at least `m` votes are ranked.
- **Length vs rating.** Movies between 40 and 240 minutes only. The scatter uses a random sample (seed fixed for reproducibility) of movies with at least 5,000 votes; the trend line is computed on all selected movies.
- **Genre mix.** A title can carry several genres, so the chart shows the share of *genre tags* per decade, not the share of movies.
- **Series runtime** is the length of an episode, not of the whole show.


## Getting started
 
Requirements: Python 3.10+ (recent versions recommended).
 
```bash
pip install marimo polars altair
```
 
Edit the notebook interactively:
 
```bash
marimo edit imdb_analysis.py
```
 
Run it as a read-only app:
 
```bash
marimo run imdb_analysis.py
```

## Project structure (notebook cells)
 
1. Imports and icon/font loading
2. Styling (CSS, KPI helper) 
3. Data loading and cleaning (`titles`)
4. Overview KPIs
5. Genre analysis (`genres_df`, best movie per genre, genre mix)
6. Runtime analysis (correlation, trend)
7. Decade analysis
8. Series rankings
9. Random pick (filters, pool, draw)

marimo notebooks are reactive: changing a slider or filter re-runs only the cells that depend on it.