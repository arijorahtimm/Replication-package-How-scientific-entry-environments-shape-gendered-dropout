# Replication package – Gendered dropout and scientific entry environments

Timm, Ari Jorah & Wittek, Mark: *Beyond access: How entry environments shape gendered dropout from scientific careers*
(working title), submitted to *Historical Social Research*, special issue "Computational Social Inequality Research in Practice".

This repository contains the code that turns the PubMed Knowledge Graph (PKG 2.0) into the author-level survival data and
estimates the Cox models reported in the article. Data files are **not** included (see *Data*).

---

## 1. Folder layout

```
code/            notebooks and scripts (steps 1–14; Python, step 2 in R; notebook outputs cleared)
data/raw/        input data (PKG 2.0, Enhanced Author Names, OpenAlex works and topic mapping) – to be downloaded, see section 7
data/derived/    intermediate files written by steps 1–11
results/         model results of step 12 (one sub-folder per specification)
figures/         figures and tables of steps 13 and 14
```

All paths are relative to the repository root; notebooks are run from `code/` (`BASE_DIR = os.path.abspath('..')`).
Folders under `data/`, `results/` and `figures/` are created automatically.

## 2. Pipeline overview

| # | file | input → output |
|---|---|---|
| 1 | `code/step01_clean_openalex_topics.py` | `raw/openalex_topics/*.csv` (OpenAlex works with PMID) → `derived/cleaned_topics.csv` (primary topic per work with subfield/field/domain and PMID) |
| 2 | `code/step02_topic_coverage.R` | `cleaned_topics.csv` → `derived/outside_topic_cites_new.csv` (mean share of references outside PubMed per topic) |
| 3 | `code/step03_build_author_paper_table.py` | PKG `raw/C02_Link_Papers_Authors.tsv.gz` + `raw/C07_Authors.tsv.gz` + `cleaned_topics.csv` (PMID → OpenAlex topic) → `derived/Final_Result.sorted.tsv` (author × paper rows with topic), `derived/Final_Result.C07_Authors.filtered.tsv` |
| 4 | `code/step04_select_topics.ipynb` | `Final_Result.sorted.tsv` + `outside_topic_cites_new.csv` → `derived/Final_Result.selected.csv` (topics with ≤ 20 % outside-PubMed citations) |
| 5 | `code/step05_restrict_period.ipynb` | `Final_Result.selected.csv` → `derived/filtered_data.csv` (1950–2023, entry < 2019) |
| 6 | `code/step06_extract_author_names.py` | `Final_Result.selected.csv` + `raw/A02_AuthorList.tsv` → `derived/author_names_pkg.tsv` (PKG names of all authors with a paper from 1950 on, all their papers) |
| 7 | `code/step07_infer_gender_pkg_names.ipynb` | `author_names_pkg.tsv` → `derived/gender_pkg_by_aid.csv` (Wiki-Gendersort on the PKG forenames, majority per AID), `derived/authors_unclassified_pkg.tsv` (authors not classified F/M/UNI) |
| 8 | `code/step08_recover_forenames.ipynb` | `authors_unclassified_pkg.tsv` + `raw/MEDLINE-enhanced-author-names-v2.tsv` → `derived/nan_ini_medline_names.csv` (match on PMID + surname, ties by first initial, then position) |
| 9 | `code/step09_infer_gender_recovered.ipynb` | → `derived/nan_ini_medline_names_and_gender.csv` (Wiki-Gendersort on the recovered forenames) |
| 10 | `code/step10_merge_gender.ipynb` | `filtered_data.csv` + steps 7 and 9 → `derived/filtered_data_recovered.csv`, `derived/gender_by_aid.csv` (gender per AID: PKG forename if F/M/UNI, otherwise recovered forename) |
| 11 | `code/step11_cox_dataprep.ipynb` | → `derived/cox_data.csv`, diagnostics, sample flow |
| 12 | `code/step12_cox_models.ipynb` | `cox_data.csv` → `results/<spec>/*.csv` |
| 13 | `code/step13_publication_graphs.ipynb` | results → model figures and LaTeX tables in `figures/models/` |
| 14 | `code/step14_descriptive_figures.ipynb` | `filtered_data_recovered.csv` + `cox_data.csv` → descriptive figures in `figures/descriptives/` |

## 3. How to run

Run the steps in the order of the table. Notes on individual steps:

- **Step 1** is a plain Python script: `cd code && python step01_clean_openalex_topics.py`.
- **Step 2** is an R script: `cd code && Rscript step02_topic_coverage.R`.
- **Step 3** is a plain Python script: `cd code && python step03_build_author_paper_table.py`.
  The PKG tables are read in chunks of 2,000,000 rows; the final sort loads `Final_Result.tsv` into memory.
- **Step 6** is a plain Python script: `cd code && python step06_extract_author_names.py` (DuckDB; spills to disk if memory is short).
- **Steps 7 and 9** need a local clone of Wiki-Gendersort; set `WG_DIR` in the first cell. A separate Python environment is recommended.
- **Step 8** runs the PKG × MEDLINE join in `N_BATCHES = 20` PMID slices with `memory_limit = '4GB'`, `threads = 2`
  (≈ 12 min). On a larger machine raise the limits / lower `N_BATCHES` – the result is identical.
- **Step 11** runtime ≈ 5–10 min, ≈ 8 GB RAM (DuckDB spills to disk). The topic × year table is kept in
  `derived/dataprep.duckdb` (its CSV export is commented out).
- **Step 12** needs a machine with a lot of memory (the main sample has 5.7 M authors; a full run takes several hours).
  Specifications can be split over several sessions via `RUN_SPECS`; each writes its own folder `results/<spec>/`.
- **Steps 13 and 14**: all figures are 10.7 cm wide, black-and-white (grey shades, line styles, hatching) and saved as
  PDF and TIFF (300 dpi). Step 13 caches the observed variable ranges in `figures/models/variable_ranges_main.csv`;
  remove this file whenever the model results are re-estimated.

### Software

R with `data.table` for step 2.
Python ≥ 3.10 with: `duckdb ≥ 1.0`, `pandas ≥ 2.0`, `numpy`, `scipy`, `lifelines ≥ 0.27`, `matplotlib ≥ 3.7` (+ Pillow for TIFF);
Wiki-Gendersort (<https://github.com/nicolasberube/Wiki-Gendersort>) for steps 7 and 9. See `requirements.txt`.

## 4. Specifications estimated in step 12

Main sample: entry 1950–2018, authors active in ≥ 2 distinct years, dropout = no publication in the 2 years after the last
one (observed by 2023). The other specifications are robustness checks.

| spec | sample / definition | models |
|---|---|---|
| `main` | entry 1950–2018 | M0–M5, M2/M3 with field strata, M2 with cohort-specific gender effects |
| `check_2002` | entry 2002–2018 (MEDLINE records full first names) | M0–M3, field strata, cohort |
| `check_pre2002` | entry 1950–2001 | M0–M3, field strata, cohort |
| `check_gap3` | dropout = 3 years without publication | M0–M3, field strata, cohort |
| `check_all_authors` | incl. authors active in one year only | M0–M3, field strata, cohort |
| `check_pkg_2002` | entry 2002–2018, only authors whose gender comes from their PKG forename (no recovered names) | M0–M3, field strata, cohort |
| `check_fs_loo` | as `main`, female share at entry **without the focal author** (`female_share_entry_loo`) | M0–M3, field strata, cohort |

Models: M0 (gender), M1 (+ entry-year strata), M2 (+ entry conditions), M3 (+ gender × entry conditions),
M4/M5 (restricted cubic splines, 4 knots at the 5/35/65/95th percentiles, without/with gender interactions).

**Gender classification:** gender is inferred from author forenames in two passes, both with Wiki-Gendersort: first from
the PKG forenames (step 7); for authors who remain unclassified (initials only or unknown name) the forename is recovered
from the Enhanced Author Names and classified again (steps 8–9). Gender per author is the majority over all their papers (step 10).

**Gender classification and career length:** before 2002 MEDLINE mostly stores initials, so PKG forenames classify mainly
authors whose careers extend beyond 2002. The name recovery (steps 8–10) closes most of this gap; classification still depends on
career length before 2002, but the female share among classified authors does not (see `diag_classification_by_entry_year_span.csv`).

## 5. Variable definitions (step 11)

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
| `gender_source` | `pkg` = F/M from the PKG forename (step 7); `recovered` = F/M from the forename recovered from MEDLINE (steps 8–9) |
| `one_year` | 1 if all publications fall in one calendar year |

Model coding (step 12): female share in 10-percentage-point units, log(1+topic size), maturity in years, first-year papers as
dummies (2, 3+; ref. 1); all continuous variables centred at the sample median.

## 6. Figures and tables

| file | notebook | content |
|---|---|---|
| `fig_classification_artifact` | 13 | F/M classification rate and female share by entry year × career span |
| `fig_gender_hr_models` | 13 | women/men HR across Models 0–5 (main) |
| `fig_gender_hr_specs` | 13 | women/men HR across models and specifications |
| `fig_gender_hr_cohorts` | 13 | women/men HR by entry period (main) |
| `fig_M3_effects`, `tab_M3_effects_by_gender.csv` | 13 | effects of entry conditions for men and women (Model 3) |
| `fig_linear_effects` | 13 | linear effects over the full observed range (Model 2 all; Model 3 men/women) |
| `fig_splines` | 13 | spline effects over the full observed range (Model 4 all; Model 5 men/women) |
| `fig_splines_gap`, `tab_gender_gap_splines.csv` | 13 | gender gap (women vs. men HR) along each entry condition (Model 5 vs. Model 3) |
| `tab_main_models.tex/.csv`, `tab_sample_flow.tex/.csv` | 13 | model table (M0–M5, main), sample construction |
| `fig_authors_gender_per_year`, `fig_female_share_entrants`, `fig_entry_distributions`, `fig_km_gender`, `fig_km_cohorts` | 14 | descriptives |

## 7. Data

Place the input files in `data/raw/`:

| file | source | access |
|---|---|---|
| `C02_Link_Papers_Authors.tsv.gz` (author–paper links), `C07_Authors.tsv.gz` (authors), `A02_AuthorList.tsv` (author names) | PubMed Knowledge Graph 2.0 (Xu et al.) | [public download](https://pubmedkg.github.io/) |
| `openalex_topics/*.csv` | OpenAlex works with a PMID (columns incl. `open_alex_work_id`, `pmid_numbers`, `topics`) | OpenAlex (Priem et al. 2022); *add snapshot date / how the works were retrieved* |
| `MEDLINE-enhanced-author-names-v2.tsv` | Enhanced Author Names (Zhang et al. 2024) | [public download](https://zenodo.org/records/10663234) |
| `openalex_topic_field_subfield_table.csv` | OpenAlex topic → subfield/field/domain mapping (Priem et al. 2022) | [public snapshot](https://docs.google.com/spreadsheets/d/1v-MAq64x4YjhO7RWcB-yrKV5D_2vOOsxl4u6GBKEXY8/edit?gid=983250122#gid=983250122) |

The derived author-level file `cox_data.csv` is deposited at *add archive/DOI*.
