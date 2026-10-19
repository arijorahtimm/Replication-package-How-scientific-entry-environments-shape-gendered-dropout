"""Step 4: select authors without a usable gender classification in the PKG.

Inputs:
  - data/derived/Final_Result.selected.csv  (output of step 2; PKG author-paper rows of the selected topics)
  - data/raw/A02_AuthorList.tsv             (PKG 2.0 author list: AID, LastName, ForeName, PMID)
Output:
  - data/derived/authors_gender_nan_ini.tsv (one row per AID x PMID, with PKG names) -> input of step 5

Selection: publications from 1950 onwards (PubYear > 1949); gender missing or coded NAN / UNK / INI.
AuthorNum and AuthorOrder are taken from the first row per AID in Final_Result.selected.csv.
The author list is read in chunks of 500,000 rows, so the script runs with moderate memory.

Usage (from the code/ folder):  python step04_select_unclassified_authors.py
"""
import os
import pandas as pd

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))   # root of the replication package
raw_dir = os.path.join(base_dir, 'data', 'raw')
derived_dir = os.path.join(base_dir, 'data', 'derived')

authorlist_path = os.path.join(raw_dir, 'A02_AuthorList.tsv')
final_result_path = os.path.join(derived_dir, 'Final_Result.selected.csv')
out_path = os.path.join(derived_dir, 'authors_gender_nan_ini.tsv')

print('loading final result', flush=True)
final_result = pd.read_csv(
    final_result_path,
    sep=',',
    dtype=str,
    usecols=['AID', 'gender', 'AuthorNum', 'AuthorOrder', 'PubYear']
)

print('filtering final result', flush=True)

final_result['PubYear'] = pd.to_numeric(
    final_result['PubYear'].str.strip(),
    errors='coerce'
)

final_result = final_result.loc[final_result['PubYear'] > 1949].copy()

final_result['AID'] = final_result['AID'].astype(str).str.strip()

gender_clean = (
    final_result['gender']
    .astype(str)
    .str.strip()
    .str.upper()
)

gender_missing_or_ini = (
    final_result['gender'].isna()
    | gender_clean.isin(['NAN', 'UNK', 'INI'])
)

filtered_aids = (
    final_result.loc[
        gender_missing_or_ini,
        ['AID', 'gender', 'AuthorNum', 'AuthorOrder']
    ]
    .drop_duplicates(subset=['AID'])
)

aid_set = set(filtered_aids['AID'])

print(f'filtered aids: {len(aid_set)}', flush=True)

print('reading authorlist in chunks', flush=True)

chunks = []

for chunk in pd.read_csv(
    authorlist_path,
    sep='\t',
    dtype=str,
    usecols=['AID', 'LastName', 'ForeName', 'PMID'],
    chunksize=500000
):
    chunk['AID'] = chunk['AID'].astype(str).str.strip()
    chunk = chunk[chunk['AID'].isin(aid_set)]

    if len(chunk) > 0:
        chunks.append(chunk)

if chunks:
    authorlist_filtered = pd.concat(chunks, ignore_index=True)
else:
    authorlist_filtered = pd.DataFrame(
        columns=['AID', 'LastName', 'ForeName', 'PMID']
    )

print(f'author rows matched: {len(authorlist_filtered)}', flush=True)

print('merging', flush=True)
result = filtered_aids.merge(authorlist_filtered, on='AID', how='left')

out_cols = [
    'AID',
    'LastName',
    'ForeName',
    'gender',
    'AuthorNum',
    'AuthorOrder',
    'PMID'
]

result = result[out_cols].drop_duplicates()

result = result.sort_values(
    ['LastName', 'ForeName', 'AID'],
    kind='mergesort'
)

print('writing output', flush=True)
result.to_csv(out_path, sep='\t', index=False)

print(f'written: {out_path}', flush=True)
print(f'rows: {len(result)}', flush=True)
