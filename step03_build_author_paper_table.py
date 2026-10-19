"""Step 3: build the PKG author-paper table with the OpenAlex topic of each paper.

Gender is not taken from the PKG; it is inferred later from the author names (steps 6-10).

Inputs:
  - data/raw/C02_Link_Papers_Authors.tsv.gz  (PKG 2.0 author-paper link table: PMID, AID, AuthorOrder, ...)
  - data/raw/C07_Authors.tsv.gz              (PKG 2.0 author table)
  - data/derived/cleaned_topics.csv          (step 1: OpenAlex works with PMID and primary topic; 'pmid_numbers', 'topics_num')
Outputs (data/derived/):
  - Final_Result.tsv                       (link rows of all papers with an OpenAlex topic, plus topics_num)
  - Final_Result.sorted.tsv                (same, sorted by topics_num, PMID, AuthorOrder) -> input of step 4
  - Final_Result.C07_Authors.filtered.tsv  (PKG author records of all AIDs in Final_Result.tsv)

The large PKG tables are read in chunks of 2,000,000 rows.

Usage (from the code/ folder):  python step03_build_author_paper_table.py
"""
import os
import pandas as pd

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))   # root of the replication package
raw_dir = os.path.join(base_dir, 'data', 'raw')
out_dir = os.path.join(base_dir, 'data', 'derived')

cleaned_topics_path = os.path.join(out_dir, 'cleaned_topics.csv')   # step 1

link_path = os.path.join(raw_dir, 'C02_Link_Papers_Authors.tsv.gz')
authors_path = os.path.join(raw_dir, 'C07_Authors.tsv.gz')

os.makedirs(out_dir, exist_ok=True)

out_path = os.path.join(out_dir, 'Final_Result.tsv')
sorted_path = os.path.join(out_dir, 'Final_Result.sorted.tsv')
authors_out = os.path.join(out_dir, 'Final_Result.C07_Authors.filtered.tsv')

chunksize = 2_000_000

# load all relevant pmids and topics
relevant = pd.read_csv(cleaned_topics_path, dtype=str)

if 'pmid_numbers' not in relevant.columns or 'topics_num' not in relevant.columns:
    raise SystemExit("cleaned_topics.csv must contain columns 'pmid_numbers' and 'topics_num'")

relevant['topics_num'] = relevant['topics_num'].astype(str).str.strip()

relevant['pmid_numbers'] = (
    relevant['pmid_numbers']
    .astype(str)
    .str.strip()
    .str.replace(r'\.0$', '', regex=True)
)

relevant = relevant[
    relevant['pmid_numbers'].notna()
    & (relevant['pmid_numbers'] != '')
    & (relevant['pmid_numbers'].str.lower() != 'nan')
]

pmid_to_topic = dict(zip(relevant['pmid_numbers'], relevant['topics_num']))
pmid_set = set(pmid_to_topic.keys())

# first pass: filter link by all pmids, add topics_num, collect used aids
used_aids = set()
first = True

for chunk in pd.read_csv(link_path, sep='\t', dtype=str, chunksize=chunksize, compression='gzip'):
    if 'PMID' not in chunk.columns or 'AID' not in chunk.columns:
        raise SystemExit('C02_Link_Papers_Authors must have columns PMID and AID')

    chunk['PMID'] = (
        chunk['PMID']
        .astype(str)
        .str.strip()
        .str.replace(r'\.0$', '', regex=True)
    )

    chunk = chunk[chunk['PMID'].isin(pmid_set)]

    if chunk.empty:
        continue

    chunk['topics_num'] = chunk['PMID'].map(pmid_to_topic).fillna('NA')

    used_aids.update(chunk['AID'].astype(str).unique().tolist())

    chunk.to_csv(
        out_path,
        sep='\t',
        index=False,
        mode=('w' if first else 'a'),
        header=first
    )

    first = False

if first:
    raise SystemExit('no rows matched your pmids, output is empty')

# second pass: filter c07_authors by used aids
first_auth = True

for chunk in pd.read_csv(authors_path, sep='\t', dtype=str, chunksize=chunksize, compression='gzip'):
    if 'AID' not in chunk.columns:
        raise SystemExit('C07_Authors must have column AID')

    chunk = chunk[chunk['AID'].astype(str).isin(used_aids)]

    if chunk.empty:
        continue

    chunk.to_csv(
        authors_out,
        sep='\t',
        index=False,
        mode=('w' if first_auth else 'a'),
        header=first_auth
    )

    first_auth = False

# final sort like sql: topics_num, pmid, authororder
df = pd.read_csv(out_path, sep='\t', dtype=str)

if 'PMID' in df.columns:
    df['PMID'] = pd.to_numeric(df['PMID'], errors='coerce')

if 'AuthorOrder' in df.columns:
    df['AuthorOrder'] = pd.to_numeric(df['AuthorOrder'], errors='coerce')

df = df.sort_values(['topics_num', 'PMID', 'AuthorOrder'], kind='mergesort')
df.to_csv(sorted_path, sep='\t', index=False)

print(f'written: {sorted_path}')
print(f'written: {authors_out}')
