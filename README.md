# Replication package – Gendered dropout and scientific entry environments

Timm, Ari Jorah & Wittek, Mark: *Beyond access: How entry environments shape gendered dropout from scientific careers*
(working title), submitted to *Historical Social Research*, special issue "Computational Social Inequality Research in Practice".

This folder contains the code that turns the PubMed Knowledge Graph (PKG 2.0) into the author-level survival data and estimates
the Cox models reported in the article. Large data files are **not** included (see *Data*).

---

## 1. Pipeline overview

| # | notebook | location in the project folder | runs on | input → output |
|---|---|---|---|---|
| 1 | `code/step1_select_topics.ipynb` | `step1_topics/select_topics.ipynb` | laptop | PKG `Final_Result.sorted.tsv` + `outside_topic_cites_new.csv` → `Final_Result.selected.csv` |
| 2 | `code/step2_restrict_period.ipynb` | `step2_descriptives/pure_dataprep.ipynb` | laptop | `Final_Result.selected.csv` → `step2_descriptives/filtered_data.csv` (1950–2023, entry < 2019) |
| 3 | `code/step3_recover_forenames_v2.ipynb` | `claude/recover_forenames_v2.ipynb` | laptop (DuckDB) | `step3_retrieve_names/authors_gender_nan_ini.tsv` + Enhanced Author Names → `claude/nan_ini_medline_names_v2.csv` (match on PMID + surname, ties by first initial, then position) |
| 4 | `code/step4_infer_gender_v2.ipynb` | `claude/infer_gender_v2.ipynb` | laptop (`wiki_env`) | → `claude/nan_ini_medline_names_and_gender_v2.csv` (Wiki-Gendersort) |
| 4b | `code/step4b_merge_recovered_gender_v2.ipynb` | `claude/merge_recovered_gender_v2.ipynb` | laptop (DuckDB) | `filtered_data.csv` + step 4 → `claude/filtered_data_recovered_v2.csv` (majority gender per AID) |
| 5 | `code/step5_cox_dataprep_v3.ipynb` | `claude/cox_dataprep_v3.ipynb` | laptop (DuckDB) | → `claude/dataprep/cox_data_v3.csv`, diagnostics, sample flow |
| 7 | `code/step7_cox_models_v3.ipynb` | `claude/cox_models_v3.ipynb` | server (lifelines) | `cox_data_v3.csv` → `results_v3/<spec>/*.csv` (copied back to `claude/results_v3/`) |
| 8 | `code/step8_publication_graphs_v3.ipynb` | `claude/publication_graphs_v3.ipynb` | laptop | results → model figures and LaTeX tables in `claude/publication_figures/` |
| 8b | `code/step8b_descriptive_figures_v3.ipynb` | `claude/descriptive_figures_v3.ipynb` | laptop | raw data + `cox_data_v3.csv` → descriptive figures in `claude/descriptives_v3/` |

The notebooks in `code/` are the analysis notebooks with cleared outputs.
Not part of the pipeline: `step6_linearregression/*` (exploratory OLS), the OpenAlex-API notebooks in `step3_retrieve_names/`
(exploratory; they contained API keys and are therefore excluded).

## 2. How to run

Paths are set in the first code cell of every notebook (`BASE_DIR` = project root `/Users/arijorah/Desktop/paper`; adapt).

1. Steps 1–2: run in order (paths point to `/Users/arijorah/Desktop/Masterarbeit/...` and must be adapted).
2. Steps 3 → 4 → 4b: run in order.
   Step 3 runs the PKG × MEDLINE join in `N_BATCHES = 20` PMID slices with `memory_limit = '4GB'`, `threads = 2`
   (≈ 12 min on a laptop; on a larger machine raise the limits / lower `N_BATCHES` – the result is identical).
   Step 4 needs Wiki-Gendersort (`WG_DIR`) and runs in its own environment (`wiki_env`).
3. Step 5: needs `claude/filtered_data_recovered_v2.csv` (step 4b) and `step2_descriptives/filtered_data.csv` (for `gender_source`).
   Runtime ≈ 5–10 min, ≈ 8 GB RAM (DuckDB spills to disk). Writes to `claude/dataprep/`.
   The topic × year table is kept in `dataprep_v3.duckdb` (its CSV export is commented out).
4. Step 7: copy `cox_data_v3.csv` (~2 GB) and the notebook to the server, set `DATA_PATH` and `OUT_DIR`, run all cells.
   Specifications can be split over several sessions via `RUN_SPECS`; each writes its own folder `OUT_DIR/<spec>/`.
   Copy the whole `results_v3` folder back to `claude/results_v3/`.
5. Steps 8 and 8b: run all cells. All figures are 10.7 cm wide, black-and-white (grey shades, line styles, hatching)
   and saved as PDF and TIFF (300 dpi). Step 8 caches the observed variable ranges in `variable_ranges_main.csv`;
   remove this file whenever the model results are re-estimated.

### Software

Python ≥ 3.10 with: `duckdb ≥ 1.0`, `pandas ≥ 2.0`, `numpy`, `scipy`, `lifelines ≥ 0.27`, `matplotlib ≥ 3.7` (+ Pillow for TIFF);
Wiki-Gendersort (<https://github.com/nicolasberube/Wiki-Gendersort>) for step 4. See `requirements.txt`.

## 3. Specifications estimated in step 7

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
whose careers extend beyond 2002. The name recovery closes most of this gap; classification still depends on career
length before 2002, but the female share among classified authors does not (see `diag_classification_by_entry_year_span.csv`).

## 4. Variable definitions (step 5)

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

Model coding (step 7): female share in 10-percentage-point units, log(1+topic size), maturity in years, first-year papers as
dummies (2, 3+; ref. 1); all continuous variables centred at the sample median.

## 5. Figures and tables

| file | notebook | content |
|---|---|---|
| `fig_classification_artifact` | 8 | F/M classification rate and female share by entry year × career span |
| `fig_gender_hr_models` | 8 | women/men HR across Models 0–5 (main) |
| `fig_gender_hr_specs` | 8 | women/men HR across models and specifications |
| `fig_gender_hr_cohorts` | 8 | women/men HR by entry period (main) |
| `fig_M3_effects`, `tab_M3_effects_by_gender.csv` | 8 | effects of entry conditions for men and women (Model 3) |
| `fig_linear_effects` | 8 | linear effects over the full observed range (Model 2 all; Model 3 men/women) |
| `fig_splines` | 8 | spline effects over the full observed range (Model 4 all; Model 5 men/women) |
| `fig_splines_gap`, `tab_gender_gap_splines.csv` | 8 | gender gap (women vs. men HR) along each entry condition (Model 5 vs. Model 3) |
| `tab_main_models.tex/.csv`, `tab_sample_flow.tex/.csv` | 8 | model table (M0–M5, main), sample construction |
| `fig_authors_gender_per_year`, `fig_female_share_entrants`, `fig_entry_distributions`, `fig_km_gender`, `fig_km_cohorts` | 8b | descriptives |

## 6. Data

| data | source | access |
|---|---|---|
| PubMed Knowledge Graph 2.0 (author–paper table with AID and gender) | Xu et al., PKG 2.0 | public download (*add DOI/URL and table name*) |
| Enhanced Author Names (MEDLINE) | Zhang et al. 2024 | public (*add DOI*) |
| OpenAlex topics and topic → subfield/field/domain mapping | OpenAlex (Priem et al. 2022) | public snapshot (*add snapshot date*) |
| Derived author-level file `cox_data_v3.csv` | this project | to be deposited (e.g. Zenodo/GESIS) – *decide* |

### Open documentation items (to complete before publication)

- exact PKG 2.0 file used for `Final_Result.sorted.tsv`, and how `authors_gender_nan_ini.tsv` and `outside_topic_cites_new.csv` were produced;
- OpenAlex snapshot date; Wiki-Gendersort version/commit;
- archive (DOI) for derived data and code;
- absolute paths in the notebooks (`/Users/arijorah/...`, server `/scratch/...`) and the working folder name `claude/` – replace by a neutral layout before deposit.
