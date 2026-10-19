"""Step 1: build the table of OpenAlex works with PMID and primary topic (cleaned_topics.csv).

Input (data/raw/openalex_topics/):
  - *.csv  OpenAlex works with a PMID, one file per download batch; columns include 'open_alex_work_id', 'num_refs',
           'num_ref_with_pmid', 'pmid_in_analytical_sample', 'publication_year', 'pmid_numbers' and 'topics'
           (the OpenAlex topics of the work as a list of dictionaries, highest-scoring topic first)
Output (data/derived/):
  - cleaned_topics.csv  one row per work: primary topic (topics_num), its subfield / field / domain id, topic name
                        (display_name) and score, plus the PMID -> input of step 3

Only the first (primary) topic of each work is kept. Topic ids are stored without the 'T' prefix
(https://openalex.org/T10673 -> 10673); subfield / field / domain as the numeric part of their OpenAlex id.

Usage (from the code/ folder):  python step01_clean_openalex_topics.py
"""
import os
import glob
from ast import literal_eval
import pandas as pd

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))   # root of the replication package
in_dir = os.path.join(base_dir, 'data', 'raw', 'openalex_topics')
out_dir = os.path.join(base_dir, 'data', 'derived')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'cleaned_topics.csv')

# all CSV files of the download (sorted, so that the row order of the output is reproducible)
csv_files = sorted(glob.glob(os.path.join(in_dir, '*.csv')))
dataframes = []


def process_dataframe(df):
    # each element of "topics" is a list of dictionaries
    df["topics"] = df["topics"].apply(literal_eval)
    # columns filled from the primary topic
    required_columns = ['id', 'display_name', 'subfield', 'field', 'domain', 'score']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    for x in range(len(df)):
        topics = df.loc[x, "topics"]
        if topics:  # "topics" is not empty
            topic = topics[0]  # primary topic
            for key, value in topic.items():
                if key in required_columns:
                    if key in ['subfield', 'field', 'domain']:
                        if isinstance(value, dict):
                            id_value = value.get('id', None)
                            if isinstance(id_value, str):
                                # numeric part of the OpenAlex id
                                df.at[x, key] = id_value.split('/')[-1]
                            else:
                                print(f"Unexpected id type for key {key} in row {x}: {id_value}")
                    else:
                        df.at[x, key] = value
    # numeric topic id of the primary topic
    df['topics_num'] = None
    for x in range(len(df)):
        topics = df.loc[x, "topics"]
        if topics:
            first_topic_id = topics[0].get('id', '')
            if isinstance(first_topic_id, str):
                first_topic_id = first_topic_id.split('/')[-1]
                df.at[x, 'topics_num'] = first_topic_id[1:] if first_topic_id.startswith('T') else first_topic_id
            else:
                print(f"Unexpected id type in topics_num for row {x}: {first_topic_id}")
    columns_to_keep = [
        'open_alex_work_id', 'num_refs', 'num_ref_with_pmid', 'pmid_in_analytical_sample',
        'subfield', 'field', 'domain', 'topics_num', 'publication_year', 'display_name', 'score',
        'pmid_numbers'
    ]
    return df[columns_to_keep]


for file in csv_files:
    chunk = pd.read_csv(file)
    dataframes.append(process_dataframe(chunk))

final_dataframe = pd.concat(dataframes, ignore_index=True)
final_dataframe.to_csv(out_path, index=False)

print(f'files read: {len(csv_files)}')
print(f'written: {out_path} ({len(final_dataframe):,} works)')
print('missing values per column:')
print(final_dataframe.isnull().sum())
