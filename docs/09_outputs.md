Output files may be aggregated including information for all samples or provided per sample. Per-sample files will be prefixed with respective aliases and represented below as {{ alias }}.

| Title | File path | Description | Per sample or aggregated |
|-------|-----------|-------------|--------------------------|
| Workflow report | wf-template-report.html | Report for all samples. | aggregated |
| Run IDs (fastq ingress) | fastq_ingress_results/{{ alias }}/fastcat_stats/run_ids | List of run IDs present in reads. | per-sample |
| Basecalling models (fastq ingress) | fastq_ingress_results/{{ alias }}/fastcat_stats/basecallers | List of basecalling models referenced in the input files. | per-sample |
| Number of reads (fastq ingress) | fastq_ingress_results/{{ alias }}/fastcat_stats/n_seqs | Number of reads returned by [fastcat](https://github.com/epi2me-labs/fastcat). | per-sample |
| Run ID counts (fastq ingress) | fastq_ingress_results/{{ alias }}/fastcat_stats/per-file-runids.tsv | File with run ID read counts. | per-sample |
| Basecallers counts (fastq ingress) | fastq_ingress_results/{{ alias }}/fastcat_stats/per-file-basecallers.tsv | TSV with per-file read counts grouped by basecaller. | per-sample |
| Per-file read stats (fastq ingress) | fastq_ingress_results/reads/fastcat_stats/per-file-stats.tsv | A TSV with per-file read stats. | per-sample |
| Read length histogram | fastq_ingress_results/{{ alias }}/fastcat_stats/length.hist | A TSV of binned read length counts representing a histogram. | per-sample |
| Read quality histogram | fastq_ingress_results/{{ alias }}/fastcat_stats/quality.hist | A TSV of binned read quality counts representing a histogram. | per-sample |
| Concatenated sequence data | fastq_ingress_results/{{ alias }}/reads.fastq.gz | Per-sample reads concatenated into one FASTQ file. | per-sample |
| Metadata JSON (fastq ingress) | fastq_ingress_results/reads/metamap.json | Per-sample metadata used in the workflow as JSON. | per-sample |
| Run IDs (xam ingress) | xam_ingress_results/{{ alias }}/bamstats_results/run_ids | List of run IDs present in input reads. | per-sample |
| Basecalling models (xam ingress) | xam_ingress_results/{{ alias }}/bamstats_results/basecallers | List of basecaller models used to basecall input reads. | per-sample |
| Number of reads (xam ingress) | xam_ingress_results/{{ alias }}/bamstats_results/n_seqs | Number of reads after running bamstats. | per-sample |
| Run ID counts (xam ingress) | xam_ingress_results/{{ alias }}/bamstats_results/bamstats.runids.tsv | TSV file containing read counts grouped by run ID. | per-sample |
| Basecalling model counts (xam ingress) | xam_ingress_results/{{ alias }}/bamstats_results/bamstats.basecallers.tsv | TSV with per-file basecaller read counts. | per-sample |
| Alignment flag stat counts | xam_ingress_results/{{ alias }}/bamstats_results/bamstats.flagstat.tsv | TSV file containing alignment flag counts per contig. | per-sample |
| Read alignment length histogram | xam_ingress_results/{{ alias }}/bamstats_results/length.hist | A TSV of binned read length counts representing a histogram. | per-sample |
| Read alignment quality histogram | xam_ingress_results/{{ alias }}/bamstats_results/quality.hist | A TSV of binned read quality counts representing a histogram. | per-sample |
| Read alignment length histogram for unmapped reads | xam_ingress_results/{{ alias }}/bamstats_results/length.unmap.hist | A TSV of binned unmapped read length counts representing a histogram. | per-sample |
| Read alignment quality histogram for unmapped reads | xam_ingress_results/{{ alias }}/bamstats_results/quality.unmap.hist | A TSV of binned unmapped read quality counts representing a histogram. | per-sample |
| Read alignment accuracy histogram | xam_ingress_results/{{ alias }}/bamstats_results/accuracy.hist | A TSV containing a histogram of the alignment accuracy of input reads. | per-sample |
| Read alignment coverage histogram | xam_ingress_results/{{ alias }}/bamstats_results/coverage.hist | A TSV containing a histogram of the alignment coverage of input reads. | per-sample |
| BAM file | xam_ingress_results/{{ alias }}/reads.bam | Per-sample reads merged and sorted in one BAM file. | per-sample |
| BAM index file | xam_ingress_results/{{ alias }}/reads.bam.bai | BAM index file resulting from ingress. | per-sample |
| Metadata JSON (xam ingress) | xam_ingress_results/reads/metamap.json | Per-sample metadata used in the workflow as JSON. | per-sample |
