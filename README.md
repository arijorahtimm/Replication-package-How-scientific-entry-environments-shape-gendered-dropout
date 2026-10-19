# Replication package – Gendered dropout and scientific entry environments

Timm, Ari Jorah & Wittek, Mark: *Beyond access: How entry environments shape gendered dropout from scientific careers*
(working title), submitted to *Historical Social Research*, special issue "Computational Social Inequality Research in Practice".

This repository contains the code that turns the PubMed Knowledge Graph (PKG 2.0) into the author-level survival data and
estimates the Cox models reported in the article. Data files are **not** included (see *Data*).

---

## 1. Folder layout

```
code/            notebooks and scripts (steps 1–11, notebook outputs cleared)
data/raw/        input data (PKG 2.0, Enhanced Author Names, OpenAlex topic mapping) – to be downloaded, see section 6
data/derived/    intermediate files written by steps 1–8
results/         model results of step 9 (one sub-folder per specification)
figures/         figures and tables of steps 10 and 11
```

All paths are relative to the repository root; notebooks are run from `code/` (`BASE_DIR = os.path.abspath('..')`).
Folders under `data/`, `results/` and `figures/` are created automatically.

## 2. Pipeline overview

| # | file | input → output |
|---|---|---|
| 1 | `code/step01_build_author_paper_table.py` | PKG `raw/C02_Link_Papers_Authors.tsv.gz` + `raw/C07_Authors.tsv.gz` + `raw/cleaned_topics.csv` (PMID → OpenAlex topic) + `raw/AID_gender_korr.csv` (gender per AID) → `derived/Final_Result.sorted.tsv` (author × paper rows with topic and gender), `derived/Final_Result.C07_Authors.filtered.tsv` |
| 2 | `code/step02_select_topics.ipynb` | `Final_Result.sorted.tsv` + `raw/outside_topic_cites_new.csv` → `derived/Final_Result.selected.csv` (topics with ≤ 20 % outside-PubMed citations) |
| 3 | `code/step03_restrict_period.ipynb` | `Final_Result.selected.csv` → `derived/filtered_data.csv` (1950–2023, entry < 2019) |
| 4 | `code/step04_select_unclassified_authors.py` | `Final_Result.selected.csv` + `raw/A02_AuthorList.tsv` → `derived/authors_gender_nan_ini.tsv` (authors with gender missing/`UNK`/`INI`, papers from 1950) |
| 5 | `code/step05_recover_forenames.ipynb` | `authors_gender_nan_ini.tsv` + `raw/MEDLINE-enhanced-author-names-v2.tsv` → `derived/nan_ini_medline_names.csv` (match on PMID + surname, ties by first initial, then position) |
| 6 | `code/step06_infer_gender.ipynb` | → `derived/nan_ini_medline_names_and_gender.csv` (Wiki-Gendersort) |
| 7 | `code/step07_merge_recovered_gender.ipynb` | `filtered_data.csv` + step 6 → `derived/filtered_data_recovered.csv` (majority gender per AID) |
| 8 | `code/step08_cox_dataprep.ipynb` | → `derived/cox_data.csv`, diagnostics, sample flow |
| 9 | `code/step09_cox_models.ipynb` | `cox_data.csv` → `results/<spec>/*.csv` |
| 10 | `code/step10_publication_graphs.ipynb` | results → model figures and LaTeX tables in `figures/models/` |
| 11 | `code/step11_descriptive_figures.ipynb` | `filtered_data_recovered.csv` + `cox_data.csv` → descriptive figures in `figures/descriptives/` |

## 3. How to run

Run the steps in the order of the table. Notes on individual steps:

- **Step 1** is a plain Python script: `cd code && python step01_build_author_paper_table.py`.
  The PKG tables are read in chunks of 2,000,000 rows; the final sort loads `Final_Result.tsv` into memory.
- **Step 4** is a plain Python script: `cd code && python step04_select_unclassified_authors.py`.
  The PKG author list is read in chunks of 500,000 rows.
- **Step 5** runs the PKG × MEDLINE join in `N_BATCHES = 20` PMID slices with `memory_limit = '4GB'`, `threads = 2`
  (≈ 12 min). On a larger machine raise the limits / lower `N_BATCHES` – the result is identical.
- **Step 6** needs a local clone of Wiki-Gendersort; set `WG_DIR` in the first cell. A separate Python environment is recommended.
- **Step 8** runtime ≈ 5–10 min, ≈ 8 GB RAM (DuckDB spills to disk). The topic × year table is kept in
  `derived/dataprep.duckdb` (its CSV export is commented out).
- **Step 9** needs a machine with a lot of memory (the main sample has 5.7 M authors; a full run takes several hours).
  Specifications can be split over several sessions via `RUN_SPECS`; each writes its own folder `results/<spec>/`.
- **Steps 10 and 11**: all figures are 10.7 cm wide, black-and-white (grey shades, line styles, hatching) and saved as
  PDF and TIFF (300 dpi). Step 10 caches the observed variable ranges in `figures/models/variable_ranges_main.csv`;
  remove this file whenever the model results are re-estimated.

### Software

Python ≥ 3.10 with: `duckdb ≥ 1.0`, `pandas ≥ 2.0`, `numpy`, `scipy`, `lifelines ≥ 0.27`, `matplotlib ≥ 3.7` (+ Pillow for TIFF);
Wiki-Gendersort (<https://github.com/nicolasberube/Wiki-Gendersort>) for step 6. See `requirements.txt`.

## 4. Specifications estimated in step 9

Main sample: entry 1950–2018, authors active in ≥ 2 distinct years, dropout = no publication in the 2 years after the last
one (observed by 2023). The other specifications are robustness checks.

| spec | sample / definition | models |
|---|---|---|
| `main` | entry 1950–2018 | M0–M5, M2/M3 with field strata, M2 with cohort-specific gender effects |
| `check_2002` | entry 2002–2018 (MEDLINE records full first names) | M0–M3, field strata, cohort |
| `check_pre2002` | entry 1950–2001 | M0–M3, field strata, cohort |
| `check_gap3` | dropout = 3 years without publication | M0–M3, field strata, cohort |
| `check_all_authors` | incl. authors active in one year only | M0–M3, field strata, cohort |
| `check_pkg_2002` | entry 2002–2018, only gender already classified in the PKG (no recovered names) | M0–M3, field strata, cohort |
| `check_fs_loo` | as `main`, female share at entry **without the focal author** (`female_share_entry_loo`) | M0–M3, field strata, cohort |

Models: M0 (gender), M1 (+ entry-year strata), M2 (+ entry conditions), M3 (+ gender × entry conditions),
M4/M5 (restricted cubic splines, 4 knots at the 5/35/65/95th percentiles, without/with gender interactions).

**Gender classification and career length:** before 2002 MEDLINE mostly stores initials, so the PKG classifies mainly authors
whose careers extend beyond 2002. The name recovery (steps 4–7) closes most of this gap; classification still depends on
career length before 2002, but the female share among classified authors does not (see `diag_classification_by_entry_year_span.csv`).

## 5. Variable definitions (step 8)

| variable | definition |
|---|---|
| `begin_year` | year of first publication (all papers of the AID) |
| `last_pubyear` | year of last publication |
| `event_gy`, `duration_gy` | dropout indicator / time for gap g ∈ {2, 3}: event if `last_pubyear + g ≤ 2023`; duration = `last_pubyear + g − begin_year` (event) or `2023 − begin_year` (censored) |
| `topics_num` | entry topic = OpenAlex topic with most papers of the author in the entry year (ties: deterministic hash) |
| `topic_size_entry` | distinct papers in the entry topic in the entry year |
| `topic_maturity_entry` | entry year − median publication year of all papers of the topic up to the entry year (data start 1950) |
| `female_share_entry` | female / (female + male) authors active in the entry topic in the entry year |
| `female_share_entry_loo`, `female_share_entrants_loo`, `female_share_entry_w` | leave-one-out (used in `check_fs_loo`) / among entrants / paper-weighted over all entry topics |
| `class_rate_entry` | share of authors in the entry topic-year with F/M classification |
| `first_year_papers` | distinct papers in the entry year |
| `gender_source` | `pkg` = F/M already in PKG; `recovered` = F/M from recovered forename + Wiki-Gendersort |
| `one_year` | 1 if all publications fall in one calendar year |

Model coding (step 9): female share in 10-percentage-point units, log(1+topic size), maturity in years, first-year papers as
dummies (2, 3+; ref. 1); all continuous variables centred at the sample median.

## 6. Figures and tables

| file | notebook | content |
|---|---|---|
| `fig_classification_artifact` | 10 | F/M classification rate and female share by entry year × career span |
| `fig_gender_hr_models` | 10 | women/men HR across Models 0–5 (main) |
| `fig_gender_hr_specs` | 10 | women/men HR across models and specifications |
| `fig_gender_hr_cohorts` | 10 | women/men HR by entry period (main) |
| `fig_M3_effects`, `tab_M3_effects_by_gender.csv` | 10 | effects of entry conditions for men and women (Model 3) |
| `fig_linear_effects` | 10 | linear effects over the full observed range (Model 2 all; Model 3 men/women) |
| `fig_splines` | 10 | spline effects over the full observed range (Model 4 all; Model 5 men/women) |
| `fig_splines_gap`, `tab_gender_gap_splines.csv` | 10 | gender gap (women vs. men HR) along each entry condition (Model 5 vs. Model 3) |
| `tab_main_models.tex/.csv`, `tab_sample_flow.tex/.csv` | 10 | model table (M0–M5, main), sample construction |
| `fig_authors_gender_per_year`, `fig_female_share_entrants`, `fig_entry_distributions`, `fig_km_gender`, `fig_km_cohorts` | 11 | descriptives |

## 7. Data

Place the input files in `data/raw/`:

| file | source | access |
|---|---|---|
| `C02_Link_Papers_Authors.tsv.gz` (author–paper links), `C07_Authors.tsv.gz` (authors), `A02_AuthorList.tsv` (author names) | PubMed Knowledge Graph 2.0 (Xu et al.) | public download (*add DOI/URL*) |
| `cleaned_topics.csv` | OpenAlex works with PMID and primary topic (`pmid_numbers`, `topics_num`) | *add source / how it was produced* |
| `AID_gender_korr.csv` | gender per PKG author ID (`AID`, `gender`) | *add source / how it was produced* |
| `outside_topic_cites_new.csv` | share of citations from outside PubMed per topic | *add source / how it was computed* |
| `MEDLINE-enhanced-author-names-v2.tsv` | Enhanced Author Names (Zhang et al. 2024) | public (*add DOI*) |
| `openalex_topic_field_subfield_table.csv` | OpenAlex topic → subfield/field/domain mapping (Priem et al. 2022) | public snapshot (*add snapshot date*) |

The derived author-level file `cox_data.csv` is deposited at *add archive/DOI*.
