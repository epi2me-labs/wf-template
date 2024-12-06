# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v5.3.3]
### Fixed
- Fixed regression in handling empty FASTQ files by updating wf-common to shabadd33adae761be6f2d59c6ecfb44b19cf472cfc to use fastcat v0.20.0

## [v5.3.2]
### Changed
- Corrected permissions for non-executable workflow_glue files in bin/.
- Updated wf-common to shaf15f9d80aba72c20e3e71f84869619873a56b8af to improve the performance of bamstats as provided by fastcat v0.19.1.
### Fixed
- getParams process cache can lead to incorrect parameter table in report if workflow is run with -resume under different conditions.

## [v5.3.1]
### Changed
- Datamodel-codegen now uses subclasses in Enum classes.
- Rename output process to publish and use publishDir if possible [CW-4137].

## [v5.3.0]
### Fixed
- Collections of sorted XAM files eligible for merge will no longer be needlessly re-sorted before merge.
### Added
- `reheader_samstream` script to be used to restore a XAM header when aligning a XAM with the `samtools bam2fq`->`minimap2` idiom.
### Changed
- Supported multiple variation files for a single XAM file in `configure_igv`.

## [v5.2.6]
### Changed
- Updated wf-common to shad28e55140f75a68f59bbecc74e880aeab16ab158 improving legends and hovers for ezCharts plots (v0.11.2).

## [v5.2.5]
### Changed
- Updated wf-common to shae58638742cf84dbeeec683ba24bcdee67f64b986 fixing `SeqSummary` and `SeqCompare` plots in ezCharts (v0.11.0).

## [v5.2.4]
### Added
- `meta` keys `src_xam` and `src_xai` pointing to the input XAM/XAI files.
- `src_xam` and `src_xai` will be set to `null` if multiple XAM per sample are provided, if files are hosted in S3 or if the files are altered by `ingress.nf`.
### Changed
- Updated wf-common to sha4a766a8333dbb72086b117c6eefba08e8ef7d76e to improve report layouts in EPI2ME Desktop with ezCharts (v0.10.2).
- Compare only SQ SN,LN,M5 when determining if collection of XAM headers have been aligned to conflicting references.
- Automatically emit the `igv.json` file upon generation.
### Fixed
- Resumed workflow leading to mismatched (BAM, BAI) validateIndex pairs when calling `xam_ingress` more than once.
- Broken Markdown rendering of install and run section of README in desktop application.

## [v5.2.3]
### Changed
- Updated wf-common image to shad399cf22079b5b153920ac39ee40095a677933f1 to include latest fastcat (v0.18.6).

## [v5.2.2]
### Changed
- Matching RG.IDs found in XAM headers are now combined across all input XAM for a particular sample and emitted once, instead of emitting new RG.IDs for each XAM file.
- Bumped wf-common to shab540ba556d0d8c38bea8fec520f0bdedd9e59520.
### Fixed
- Non-determinstic catting and merging of XAM files during ingress.

## [v5.2.1]
### Changed
- Updated `epi2melabs` to v0.0.56 to allow schemas without a `demo_url` field.

## [v5.2.0]
### Added
- Support for CRAM alignment format when creating IGV config files.
- Support for an optional "analysis_groups" column in the sample sheet providing grouping information for the input samples.
### Changed
- Basecall models are now obtained from FASTQ / BAM input files via fastcat / bamstats output and added to sample meta map.

## [v5.1.4]
### Added
- Support for creating IGV JSON config files.
### Changed
- Updated `ezcharts` to v0.9.1, showing coverage and accuracy plots when available.

## [v5.1.3]
### Changed
- `workflow-glue` CLI bootstrapping amended to skip imports of all components when not required.

## [v5.1.2]
### Added
- `xam_ingress` reads `basecall_model` and `runid` to metamap from RG DS tags.

## [v5.1.1]
### Fixed
- `xam_ingress` failing on BAM files that are lacking a `@HD` line in the header.

## [v5.1.0]
### Added
- Functionality to allow chunking of fastq outputs from ingress. Additional keys in meta information are added to reflect this.
### Changed
- Use 4 threads for bgzip compressions during fastcat process.
- Updated fastcat to v0.17.0 for faster decompression and on-the-fly run ID summary.
- Updated to use ezCharts v0.8.0 for report generation.
- Remove per-read stats from fastcat output by default.
### Fixed
- Ingress code would return stats even when not requested.

## [v5.0.4]
### Fixed
- `xam_ingress` failing to stage S3 BAM indexes.

## [v5.0.3]
### Changed
- Bumped wf-common to sha645176f98b8780851f9c476a064d44c2ae76ddf6.
### Fixed
- Refusing to parse valid sample sheet CSV files in certain cases.

## [v5.0.2]
### Changed
- Bumped wf-common to sha362c808b4f22ce66f940bef192a1316aec5f4c75.

## [v5.0.1]
### Added
- `container` directive for processes with `wftemplate` label.
- Missing label directives for `samtools_index` process.
### Changed
- Bumped wf-common to shaa0c37a1cad3357e2b5c6fa8b9ebc25ee9ee88879.

## [v5.0.0]
### Added
- Argument `return_fastq` to `xam_ingress()` to convert the input BAM data to FASTQ format.
- User provided sample sheet is now published in the output directory as `sample_sheet.csv`.
- A check to make sure the sample sheet is a CSV file (and not e.g. `.xlsx`).
- `n_seqs` field to the meta map for `fastq_ingress()`, containing the number of processed reads of the respective sample. 
- `n_primary` and `n_unmapped` for `xam_ingress()`, containing the number of primary alignments and unmapped reads for the respective sample.
- Support for indexing of input BAM files within `xam_ingress()`.
### Changed
- Update bug template to new workflow execution possibilities.
- `--client_fields` parameter to allow input of a JSON file of key value pairs to display on output reports.
- Pre-indexed, single BAM files are not sorted within `xam_ingress()`.


## [v4.3.0]
### Changed
- Bumped minimum required Nextflow version to 23.04.2.
- Renamed `lib/fastqingress.nf` to `lib/ingress.nf` to reflect its expanded functionality.
- The documentation has been updated.
### Added
- `xam_ingress` function for processing (u)BAM data.
- Git issue bug form requires user to report if the demo data was successful.
### Removed
- Default local executor CPU and RAM limits.


## [v4.2.0]
### Added
- 'CWUtil.mutateParam(params, k, v)' can be used to mutate the contents of the global Nextflow parameter map
### Changed
- Workflow uses `wf-common` container by default
- Sample `meta` contains `run_ids` key which lists all Run IDs observed by `fastcat`
- `fastqingress` processes additionally labelled with `fastq_ingress`
- Use literal names to stage process inputs wherever possible and wrap filenames in quotes otherwise.
- Any sample aliases that contain spaces will be replaced with underscores.
### Removed
- `wf-template` container is no longer used
- `params.process_label` is no longer required

## [v4.1.0]
### Added
- Optional `required_sample_types` field added to fastqingress. The sample sheet must contain at least one of each sample type provided to be deemed valid.
- Configuration for running demo data in AWS
### Changed
- Updated GitHub issue templates to force capture of more information.
- Removed glibc hack from post-test script
- Updated LICENSE to BSD-4-Clause
- Enum choices are enumerated in the `--help` output
- Enum choices are enumerated as part of the error message when a user has selected an invalid choice
- Bumped minimum required Nextflow version to 22.10.8
### Fixed
- Replaced `--threads` option in fastqingress with hardcoded values to remove warning about undefined `param.threads`

## [v4.0.0]
### Added
- GitHub issues template.
- Return of metadata with fastqingress.
- Check of number of samples and barcoded directories.
- Example of how to use the metadata from `fastqingress`.
- Implemented `--version`
- `fastcat_extra_args` option to `fastq_ingress` to pass arbitrary arguments to `fastcat` (defaults to empty string).
- `fastcat_stats` option to `fastq_ingress` to force generation of `fastcat` stats even when the input is only a single file (default is false).
### Changed
- Use `bgzip` for compression instead of `pigz`.
- pre-commit now uses `flake8` v5.0.4.
- Report is now created with [ezCharts](https://github.com/epi2me-labs/ezcharts).
- The workflow now also publishes the metadata emitted by `fastq_ingress` in `$params.out_dir`.
- `fastq_ingress` now returns `[metamap, path-to-fastcat-seqs | null, path-to-fastcat-stats | null]`.
- Bumped base container to v0.2.0.
- Use groovy script to ping after workflow has run.
- Removed sanitize fastq option.
- fastq_ingress now removes unclassified read folders by default.
- Workflow name and version is now more prominently displayed on start
### Fixed
- Output argument in Fastqingress homogenised.
- Sanitize fastq intermittent null object error.
- Add `*.pyc` and `*.pyo` ignores to wf-template .gitignore
### Note
- Bumped version to `v4` to align versioning with Launcher v4

## [v0.2.0]
### Added
- default process label parameter
- Added `params.wf.example_cmd` list to populate `--help`
### Changed
- Update WorkflowMain.groovy to provide better `--help`

## [v0.1.0]
### Changed
- `sample_name` to `sample_id` throughout to mathc MinKNOW samplesheet.
### Added
- Singularity profile include in base config.
- Numerous other changes that have been lost to the mists of time.

## [v0.0.7]
### Added
- Fastqingress module for common handling of (possibly multiplexed) inputs.
- Optimized container size through removal of various conda cruft.
### Changed
- Use mamba by default for building conda environments.
- Cut down README to items specific to workflow.
### Fixed
- Incorrect specification of conda environment file in Nextflow config.

## [v0.0.6]
### Changed
- Explicitely install into base conda env

## [v0.0.5]
### Added
- Software versioning report example.

## [v0.0.4]
### Changed
- Version bump to test CI.

## [v0.0.3]
### Changed
- Moved all CI to templates.
- Use canned aplanat report components.

## [v0.0.2]
### Added
- CI release checks.
- Create pre-releases in CI from dev branch.

## [v0.0.1]
* First release.

