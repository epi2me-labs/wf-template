### Input Options

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| fastq | string | FASTQ files to use in the analysis. | This accepts one of four cases: (i) the path to a single FASTQ file; (ii) the path to a folder containing FASTQ files; (iii) the path to a folder containing one level of sub-folders which in turn contain FASTQ files; (iv) the path to a MinKNOW experiment folder containing sub-folders for each sequenced sample. In the first and second case, a sample name can be supplied with `--sample`. In the third case, the data is assumed to be multiplexed with the names of the sub-folders as barcodes, and a sample sheet can be provided with `--sample_sheet`. In the fourth case, the data is assumed to be multiplexed with the names of the sub-folders as samples, and a sample sheet and/or sample name must be provided to indicate which samples to analyse. |  |
| bam | string | BAM or unaligned BAM (uBAM) files to use in the analysis. | This accepts one of four cases: (i) the path to a single BAM file; (ii) the path to a folder containing BAM files; (iii) the path to a folder containing one level of sub-folders which in turn contain BAM files; (iv) the path to a MinKNOW experiment folder containing sub-folders for each sequenced sample. In the first and second case, a sample name can be supplied with `--sample`. In the third case, the data is assumed to be multiplexed with the names of the sub-folders as barcodes, and a sample sheet can be provided with `--sample_sheet`. In the fourth case, the data is assumed to be multiplexed with the names of the sub-folders as samples, and a sample sheet and/or sample name must be provided to indicate which samples to analyse. |  |
| analyse_unclassified | boolean | Analyse unclassified reads from input folder. By default the workflow will not process reads in the unclassified folder. | If selected and if the input is a multiplex folder the workflow will also process the unclassified folder. | False |
| analyse_fail | boolean | Analyse failed reads from input folder. By default the workflow will not process reads in a pod5_fail, bam_fail or fastq_fail sub-folders. | If selected and if the input is a multiplex folder the workflow will also process pod5_fail, bam_fail and fastq_fail folders. | False |
| watch_path | boolean | Enable to continuously watch the input directory for new input files. | This option enables the use of Nextflow’s directory watching feature to constantly monitor input directories for new files. | False |
| fastq_chunk | integer | Sets the maximum number of reads per chunk returned from the data ingress layer. | Default is to not chunk data and return a single FASTQ file. |  |


### Sample Options

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| sample_sheet | string | A CSV file used to map barcodes to sample aliases. The sample sheet can be provided when the input data is a folder containing sub-folders with FASTQ files. | The sample sheet is a CSV file with, minimally, columns named `barcode` and `alias`. Extra columns are allowed. A `type` column is required for certain workflows and should have the following values; `test_sample`, `positive_control`, `negative_control`, `no_template_control`. An optional `analysis_group` column is used by some workflows to combine the results of multiple samples. If the `analysis_group` column is present, it needs to contain a value for each sample. |  |
| sample | string | A single sample name for singleplexed data. For multiplex data, this will limit analysis to the single named sample. |  |  |


### Output Options

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| out_dir | string | Directory for output of all workflow results. |  | output |


