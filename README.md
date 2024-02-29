# Metagenomics summary report tool
A script for meta-analysing a set of runs from the CIDR metagenomics workflow, producing an XLSX spreadsheet for further analysis.

Activate the 'cmg' conda environment before running. The recepie for this environment can be found [on the CIDR metageomics workflow Git ](https://github.com/GSTT-CIDR/metagenomics_workflow/blob/main/conda/cmg.txt).

## Instructions for use
Activate the cmg conda environment
```conda activate cmg```

### Arguments
- `--sample_names_file`: Path to the file containing a list of sample names. Each sample name should be on a separate line and must match the names used in the sample sheet for the metagenomics pipeline.
- `--results_dir`: Directory path where the results are stored.
- `--output_excel`: File path for the output Excel file.
- `--abundance_threshold`: (Optional) Minimum abundance threshold for filtering. Defaults to 1 if not specified.

### Example
```python metagenomics_summary_report.py --sample_names_file sample_names.txt --results_dir /path/to/results --output_excel summary.xlsx --abundance_threshold 5```
