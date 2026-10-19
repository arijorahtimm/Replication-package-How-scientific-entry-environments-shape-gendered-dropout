"""Step 6: extract the PKG names of all authors in the sample.

Inputs:
  - data/derived/Final_Result.selected.csv  (output of step 4; PKG author-paper rows of the selected topics)
  - data/raw/A02_AuthorList.tsv             (PKG 2.0 author list: AID, LastName, ForeName, PMID)
Output:
  - data/derived/author_names_pkg.tsv       (one row per AID x PMID: AID, LastName, ForeName, AuthorNum, AuthorOrder, PMID)
                                            -> input of step 7 (gender from PKG forenames) and, for unclassified
                                               authors, of step 8 (forename recovery)

Selection: all authors (AID) with at least one paper from 1950 onwards in Final_Result.selected.csv. For these authors all
rows of the PKG author list are kept (all their papers, also outside the selected topics), so that the gender vote and
the forename recovery can use every paper of an author. AuthorNum and AuthorOrder are taken from the same author x paper
row of Final_Result.selected.csv (NULL for papers outside the selected topics).

Runs with DuckDB (spills to disk if memory is short). Usage (from the code/ folder):
    python step06_extract_author_names.py
"""
import os
import duckdb

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))   # root of the replication package
raw_dir = os.path.join(base_dir, 'data', 'raw')
derived_dir = os.path.join(base_dir, 'data', 'derived')

authorlist_path = os.path.join(raw_dir, 'A02_AuthorList.tsv')
final_result_path = os.path.join(derived_dir, 'Final_Result.selected.csv')
out_path = os.path.join(derived_dir, 'author_names_pkg.tsv')

con = duckdb.connect()
con.execute("SET preserve_insertion_order = false")
con.execute(f"SET temp_directory = '{os.path.join(derived_dir, 'duckdb_tmp')}'")

# integer ids: the CSV files may store ids as '123' or '123.0'
ID = "TRY_CAST(TRY_CAST(trim({}) AS DOUBLE) AS BIGINT)"

print('selecting authors and their positions on the selected papers', flush=True)
con.execute(f"""
CREATE OR REPLACE TABLE sel AS
SELECT
    {ID.format('AID')}                                   AS aid,
    {ID.format('PMID')}                                  AS pmid,
    min(TRY_CAST(TRY_CAST(AuthorNum AS DOUBLE) AS INTEGER))   AS AuthorNum,
    min(TRY_CAST(TRY_CAST(AuthorOrder AS DOUBLE) AS INTEGER)) AS AuthorOrder,
    max(TRY_CAST(trim(PubYear) AS DOUBLE))               AS pubyear
FROM read_csv('{final_result_path}', header = true, all_varchar = true)
GROUP BY 1, 2
""")
con.execute("""
CREATE OR REPLACE TABLE aids AS
SELECT DISTINCT aid FROM sel WHERE pubyear > 1949 AND aid IS NOT NULL AND aid <> 0
""")
print(f"authors: {con.execute('SELECT count(*) FROM aids').fetchone()[0]:,}", flush=True)

print('reading the PKG author list and writing output', flush=True)
con.execute(f"""
COPY (
    SELECT DISTINCT
        a.aid           AS AID,
        a.LastName,
        a.ForeName,
        s.AuthorNum,
        s.AuthorOrder,
        a.pmid          AS PMID
    FROM (
        SELECT {ID.format('AID')} AS aid, {ID.format('PMID')} AS pmid, LastName, ForeName
        FROM read_csv('{authorlist_path}', delim = '\\t', header = true, all_varchar = true)
    ) a
    JOIN aids USING (aid)
    LEFT JOIN sel s ON s.aid = a.aid AND s.pmid = a.pmid
) TO '{out_path}' (HEADER, DELIMITER '\\t')
""")

n_rows, n_aids = con.execute(
    f"SELECT count(*), count(DISTINCT AID) FROM read_csv('{out_path}', delim = '\\t', header = true)").fetchone()
print(f'written: {out_path}', flush=True)
print(f'rows: {n_rows:,}, authors: {n_aids:,}', flush=True)
