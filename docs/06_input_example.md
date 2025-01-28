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

