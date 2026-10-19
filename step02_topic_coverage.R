# Step 2: coverage of each OpenAlex topic by PubMed (outside_topic_cites_new.csv)
#
# For every work, the share of its references that point outside PubMed is 1 - (references with PMID / all references).
# The topic-level share is the mean over all works of the topic. Step 4 keeps only topics in which this share is <= 20 %.
# Topics whose works have no reference information get NA (mostly topics with only a few papers).
#
# Input:  data/derived/cleaned_topics.csv          (step 1; columns num_refs, num_ref_with_pmid, topics_num, display_name)
# Output: data/derived/outside_topic_cites_new.csv (columns topics_num, display_name, share_outside_PubMed_per_topic)
#
# Usage (from the code/ folder):  Rscript step02_topic_coverage.R

library(data.table)

base_dir    <- normalizePath("..")                     # root of the replication package
derived_dir <- file.path(base_dir, "data", "derived")

# Load information on OpenAlex topics
open_alex_info <- fread(file.path(derived_dir, "cleaned_topics.csv"))

# Share of references pointing outside PubMed, per work
open_alex_info[, share_outside_PubMed_refs := 1 - (num_ref_with_pmid / num_refs)]
summary(open_alex_info$share_outside_PubMed_refs)

# Share of references pointing outside PubMed, mean per topic
open_alex_info[, share_outside_PubMed_per_topic := mean(share_outside_PubMed_refs, na.rm = TRUE), by = topics_num]

# One row per topic
topic_info_unique <- unique(open_alex_info, by = "topics_num")
topic_info_unique <- topic_info_unique[, c("topics_num", "display_name", "share_outside_PubMed_per_topic")]
summary(topic_info_unique$share_outside_PubMed_per_topic)

fwrite(topic_info_unique, file.path(derived_dir, "outside_topic_cites_new.csv"))
cat("written:", file.path(derived_dir, "outside_topic_cites_new.csv"), "(", nrow(topic_info_unique), "topics )\n")
