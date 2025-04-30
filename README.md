# Template workflow

Nextflow workflow template repository.



## Introduction

<!---This section of documentation typically contains a list of things the workflow can perform also any other intro.--->

This workflow is not intended to be used by end users.

This workflow can be used for the following:

+ As a template using gitlabs create project from template.
+ For testing of any scripts that are the same across workflows such as scripts in the lib directory.



## Compute requirements

Recommended requirements:

+ CPUs = 2
+ Memory = 2GB

Minimum requirements:

+ CPUs = 2
+ Memory = 2GB

Approximate run time: 5 minutes per sample

ARM processor support: True




## Install and run


These are instructions to install and run the workflow on command line.
You can also access the workflow via the
[EPI2ME Desktop application](https://labs.epi2me.io/downloads/).

The workflow uses [Nextflow](https://www.nextflow.io/) to manage
compute and software resources,
therefore Nextflow will need to be
installed before attempting to run the workflow.

The workflow can currently be run using either
[Docker](https://docs.docker.com/get-started/)
or [Singularity](https://docs.sylabs.io/guides/3.0/user-guide/index.html)
to provide isolation of the required software.
Both methods are automated out-of-the-box provided
either Docker or Singularity is installed.
This is controlled by the
[`-profile`](https://www.nextflow.io/docs/latest/config.html#config-profiles)
parameter as exemplified below.

It is not required to clone or download the git repository
in order to run the workflow.
More information on running EPI2ME workflows can
be found on our [website](https://labs.epi2me.io/wfindex).

The following command can be used to obtain the workflow.
This will pull the repository in to the assets folder of
Nextflow and provide a list of all parameters
available for the workflow as well as an example command:

```
nextflow run epi2me-labs/wf-template --help
```
To update a workflow to the latest version on the command line use
the following command:
```
nextflow pull epi2me-labs/wf-template
```

A demo dataset is provided for testing of the workflow.
It can be downloaded and unpacked using the following commands:
```
wget https://ont-exd-int-s3-euwst1-epi2me-labs.s3.amazonaws.com/wf-template/wf-template-demo.tar.gz
tar -xzvf wf-template-demo.tar.gz
```
The workflow can then be run with the downloaded demo data using:
```
nextflow run epi2me-labs/wf-template \
	--fastq 'wf-template-demo/test_data/reads.fastq.gz' \
	-profile standard
```

For further information about running a workflow on
the command line see https://labs.epi2me.io/wfquickstart/




## Related protocols

<!---Hyperlinks to any related protocols that are directly related to this workflow, check the community for any such protocols.--->

This workflow is designed to take input sequences that have been produced from [Oxford Nanopore Technologies](https://nanoporetech.com/) devices.

Find related protocols in the [Nanopore community](https://community.nanoporetech.com/docs/).



## Input example

<!---Example of input folder structure, delete and edit as appropriate per workflow.--->
This workflow accepts either FASTQ or BAM files as input.


### Single file

A single FASTQ or BAM file can be provided to ingress and will be analysed by the workflow.
A sample name can optionally be supplied with the `sample` option, otherwise the file name before any file extensions will be used.

### Single folder containing files

A single folder containing FASTQ or BAM files can be provided to ingress.
The workflow will merge these files together and analyse them as one sample.

A sample name can optionally be supplied with the `sample` option, otherwise the folder name will be used.

```
─── input_folder
    ├── reads0.fastq
    └── reads1.fastq
```

### Multiple folders containing files

A folder containing one level of sub-folders which in turn contain FASTQ or BAM files.
The anticipated use case here is for demultiplexed barcodes.

```
─── input_folder
    ├── barcode01
    │   ├── reads0.fastq
    │   └── reads1.fastq
    ├── barcode02
    │   ├── reads0.fastq
    │   ├── reads1.fastq
    │   └── reads2.fastq
    ├── barcode03
    │   └── reads0.fastq
    └── unclassified
        └── reads0.fastq
```

The names of the folders will be used as the names of each multiplexed sample.
The workflow will merge all files found inside each of the sub-folders into distinct samples for analysis.
The folders may have any name, however folders named `unclassified` will be ignored by ingress unless the `analyse_unclassified` option is switched on.


### Multiple folders containing MinKNOW sample folders with BAM files

A folder containing more than one level of folders.
The anticipated use case here is for analysing a MinKNOW experiment folder where the output format is BAM files.
FASTQ files are not supported in this layout at this time.

```
─── input_folder
    ├── sample01
    │   ├── YYYYMMDD_HHMM_0A_FLO00000_00000000
    │   │   ├── bam_pass
    │   │   │   ├── reads0.bam
    │   │   │   └── reads1.bam
    │   │   └── bam_fail
    │   │       └── reads0.bam
    │   ├── YYYYMMDD_HHMM_0B_FLO11111_11111111
    │   │   ├── bam_pass
    │   │   │   └── reads0.bam
    │   │   └── bam_fail
    └── sample02
        └── YYYYMMDD_HHMM_0C_FLO22222_22222222
            ├── bam_pass
            │   └── reads0.bam
            └── bam_fail
                └── reads0.bam
```

The names of the first-level sub-folders will be used as the names of each multiplexed sample.
Files must appear at the same level in the file tree.
The workflow will recursively merge all files found inside each of the first-level sub-folders into distinct samples for analysis.

All the files in the example above have a depth of four; and so will be analysed by the workflow.
It would be an error to place files in other levels, for example below `bad_sample01` has files at a depth of four and `bad_sample02` has files at a depth of two:

```
─── bad_input_folder
    ├── bad_sample01
    │   └── YYYYMMDD_HHMM_0A_FLO00000_00000000
    │       └── bam_pass
    │           ├── reads0.bam
    │           └── reads1.bam
    └── bad_sample02
        └── reads0.bam
```

To ensure the workflow will analyse the intended samples you must indicate to the workflow the samples to analyse in one of three ways:
* `sample_sheet`: A sample sheet describing samples in the input folder to be processed. The folder names must match the barcodes or sample aliases as specified in the sample sheet.
* `sample`: A single sample name that matches one of the sample folders in the input folder.
* Both `sample_sheet` and `sample`: This will consume all metadata from the sample sheet but limit analysis to the single named sample.

Additionally, the following rules apply when ingress is searching for files to be analysed by the workflow:
* Sub-folders beyond the first-level named `pod5_fail`, `fastq_fail` and `bam_fail` will be ignored by ingress unless the  `analyse_fail` option is switched on.
* Sub-folders beyond the first-level named `unclassified` will be ignored by ingress unless the `analyse_unclassified` option is switched on. It is not possible to name a sample `unclassified` using the sample sheet.
* It is an error to provide folders matching both the barcode and alias for a sample's row in the sample sheet.
* Is is an error to provide a sample sheet where a sample alias begins with the word "barcode".





## Input parameters

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






## Outputs

Output files may be aggregated including information for all samples or provided per sample. Per-sample files will be prefixed with respective aliases and represented below as {{ alias }}.

| Title | File path | Description | Per sample or aggregated |
|-------|-----------|-------------|--------------------------|
| workflow report | ./wf-template-report.html | Report for all samples | aggregated |
| Per file read stats | ./fastq_ingress_results/reads/fastcat_stats/per-file-stats.tsv | A TSV with per file read stats, including all samples. | aggregated |
| Per read stats | ./fastq_ingress_results/reads/fastcat_stats/per-read-stats.tsv | A TSV with per read stats, including all samples. | aggregated |
| Run ID's | ./fastq_ingress_results/reads/fastcat_stats/run_ids | List of run ID's present in reads. | aggregated |
| Meta map json | ./fastq_ingress_results/reads/metamap.json | Meta data used in workflow presented in a JSON. | aggregated |
| Concatenated sequence data | ./fastq_ingress_results/reads/{{ alias }}.fastq.gz | Per sample reads concatenated in to one fastq file. | per-sample |




## Pipeline overview

<!---High level numbered list of main steps of the workflow and hyperlink to any tools used. If multiple workflows/different modes perhaps have subheadings and numbered steps. Use nested numbering or bullets where required.--->
### 1. Concatenates input files and generate per read stats.

The [fastcat/bamstats](https://github.com/epi2me-labs/fastcat) tool is used to concatenate multifile samples to be processed by the workflow. It will also output per read stats including average read lengths and qualities.



## Troubleshooting

<!---Any additional tips.--->
+ If the workflow fails please run it with the demo data set to ensure the workflow itself is working. This will help us determine if the issue is related to the environment, input parameters or a bug.
+ See how to interpret some common nextflow exit codes [here](https://labs.epi2me.io/trouble-shooting/).



## FAQ's

<!---Frequently asked questions, pose any known limitations as FAQ's.--->

If your question is not answered here, please report any issues or suggestions on the [github issues](https://github.com/epi2me-labs/wf-template/issues) page or start a discussion on the [community](https://community.nanoporetech.com/).



## Related blog posts

+ [Importing third-party workflows into EPI2ME Labs](https://labs.epi2me.io/nexflow-for-epi2melabs/)

See the [EPI2ME website](https://labs.epi2me.io/) for lots of other resources and blog posts.



