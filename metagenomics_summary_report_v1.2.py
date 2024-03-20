import pandas as pd
import glob
import os
from collections import Counter
import re
import taxonomy
import csv
import argparse
from styleframe import StyleFrame

# Setup argparse
parser = argparse.ArgumentParser(description='The script produces a summary of outputs from the metagenomics pipeline in XLSX format. Sample names should be provided to the script one per line and must be identical to the sample names in the sample_sheet used to launch the metagnomics pipeline.')
parser.add_argument('--sample_names_file', type=str, help='File path to the list of sample names.')
parser.add_argument('--results_dir', type=str, help='Directory path for the results.')
parser.add_argument('--output_excel', type=str, help='Output file path for the Excel file.')
parser.add_argument('--abundance_threshold', type=float, default=1.0, help='Minimum abundance threshold for filtering (default: 1.0).')

args = parser.parse_args()


# Replace hardcoded paths with arguments
NODES = "./db/ref/refseq/taxonomy/nodes.dmp"
NAMES = "./db/ref/refseq/taxonomy/names.dmp"
tax = taxonomy.Taxonomy.from_ncbi(NODES, NAMES)


def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def get_genus(taxID, tax):
    try:
        genus = tax.parent(str(taxID), at_rank="genus")
        return int(genus.id)
    except:
        return "None"

# Reading sample names from the file specified in the command line
sample_names = []
with open(args.sample_names_file, 'r') as file:
    for line in file:
        sample_names.append(line.strip())

print(sample_names)

def check_directories(dir_list):
    existing_dirs = []
    non_existing_dirs = []
    for directory in dir_list:
        if os.path.isdir(directory):
            existing_dirs.append(directory)
        else:
            non_existing_dirs.append(directory)
    return existing_dirs, non_existing_dirs

# Use results_dir from arguments
sample_paths = [os.path.join(args.results_dir, sample) for sample in sample_names]
existing, non_existing = check_directories(sample_paths)

files = existing
files.sort(key=natural_keys)

print(non_existing)

### TIMEPOINTS TO EXTRACT DATA FROM
time_points = [0.5, 1, 2, 16, 24]


# Use abundance_threshold from arguments
threshold = args.abundance_threshold

## CREATES DATAFRAME OF RESULTS
results = dict()
for f in files:
    sample = f.split("/")[-1]
    results[sample] = {}
    for time in time_points:
        bac_path = f"{f}/{time}_hours/centrifuge/bacterial_centrifuge_report.tsv"
        read_stats_path = f"{f}/{time}_hours/host/{sample}_{time}_hours_map_stats.txt"
        # Read the mapping statistics
        if os.path.exists(read_stats_path):
            with open(read_stats_path, 'r') as stats_file:
                total_reads = int(stats_file.readline().strip())
                human_reads = int(stats_file.readline().split('/')[0].strip())
        else:
            total_reads, human_reads = 0, 0
            
        # Calculate the percentage of human and microbial reads
        if total_reads > 0:
            human_reads_percentage = round((human_reads / total_reads) * 100, 1)

        if os.path.exists(bac_path):
            df = pd.read_csv(bac_path, sep="\t")
            total_counts = df["Counts"].sum()
            df["Percentage"] = round(df["Counts"] / total_counts * 100, 3)
            df = df[(df["Percentage"] >= threshold) | (df["Organism"].str.contains("Candida|Aspergillus|Mycoplasma|Legionella|Chlamydia|Pneumocystis|Mycobacterium|Mycobacteroides"))]
            df = df[["Organism", "Counts", "Percentage"]]
            organisms, counts, percentage = df.apply(lambda x: "\n".join([str(i) for i in x]))
        else:
            total_counts, organisms, counts, percentage = 0, 0, 0, 0
        
        ## viral
        read_path = f"{f}/{time}_hours/centrifuge/viral_centrifuge_report.tsv"
        # Initialize virus and v_counts
        virus, v_counts = 0, 0

        if os.path.exists(read_path):
            read_df = pd.read_csv(read_path, sep="\t")
            if not read_df.dropna().empty:
                read_df = read_df[["Organism", "Counts"]]
                virus, v_counts = read_df.apply(lambda x: "\n".join([str(i) for i in x]))

        # Update the results dictionary with the new metrics
        results[sample].update({
            f"Total Reads {time} hrs": total_reads,
            f"Human Reads {time} hrs": human_reads,
            f"Human Reads Percentage {time} hrs": human_reads_percentage,
            f"Total classified {time} hrs": total_counts,
            f"Organisms {time} hrs": organisms,
            f"Counts {time} hrs": counts,
            f"Organism percentage abundance {time} hrs": percentage,
            f"Viral organism {time} hrs": virus,
            f"Viral counts {time} hrs": v_counts
        })




# Reset the index to make the sample names a regular column instead of the index
master = pd.DataFrame.from_dict(results, orient="index").reset_index()

# Rename the new column to "Sample" to clearly indicate what it represents
master.rename(columns={'index': 'Sample'}, inplace=True)

# Continue with the rest of your script
# Example: Replace '\r' with '\n' in the entire DataFrame for correct line breaks in Excel
master = master.replace('\r', '\n')

# Write to Excel with StyleFrame for correct line breaks
StyleFrame(master).to_excel(args.output_excel).save()
