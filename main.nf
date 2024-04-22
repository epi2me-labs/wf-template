#!/usr/bin/env nextflow

// Developer notes
//
// This template workflow provides a basic structure to copy in order
// to create a new workflow. Current recommended practices are:
//     i) create a simple command-line interface.
//    ii) include an abstract workflow scope named "pipeline" to be used
//        in a module fashion
//   iii) a second concrete, but anonymous, workflow scope to be used
//        as an entry point when using this workflow in isolation.

import groovy.json.JsonBuilder
nextflow.enable.dsl = 2

include { fastq_ingress; xam_ingress } from './lib/ingress'
include {
    getParams;
} from './lib/common'


OPTIONAL_FILE = file("$projectDir/data/OPTIONAL_FILE")

process getVersions {
    label "wftemplate"
    cpus 1
    output:
        path "versions.txt"
    script:
    """
    python -c "import pysam; print(f'pysam,{pysam.__version__}')" >> versions.txt
    fastcat --version | sed 's/^/fastcat,/' >> versions.txt
    """
}


process makeReport {
    label "wftemplate"
    input:
        val metadata
        tuple path(stats, stageAs: "stats_*"), val(no_stats)
        path client_fields
        path "versions/*"
        path "params.json"
        val wf_version
    output:
        path "wf-template-*.html"
    script:
        String report_name = "wf-template-report.html"
        String metadata = new JsonBuilder(metadata).toPrettyString()
        String stats_args = no_stats ? "" : "--stats $stats"
        String client_fields_args = client_fields.name == OPTIONAL_FILE.name ? "" : "--client_fields $client_fields"
    """
    echo '${metadata}' > metadata.json
    workflow-glue report $report_name \
        --versions versions \
        $stats_args \
        $client_fields_args \
        --params params.json \
        --metadata metadata.json \
        --wf_version $wf_version
    """
}


// See https://github.com/nextflow-io/nextflow/issues/1636. This is the only way to
// publish files from a workflow whilst decoupling the publish from the process steps.
// The process takes a tuple containing the filename and the name of a sub-directory to
// put the file into. If the latter is `null`, puts it into the top-level directory.
process output {
    // publish inputs to output directory
    label "wftemplate"
    publishDir (
        params.out_dir,
        mode: "copy",
        saveAs: { dirname ? "$dirname/$fname" : fname }
    )
    input:
        tuple path(fname), val(dirname)
    output:
        path fname
    """
    """
}

// Creates a new directory named after the sample alias and moves the ingress results
// into it.
process collectIngressResultsInDir {
    label "wftemplate"
    input:
        // both inputs might be `OPTIONAL_FILE` --> stage in different sub-directories
        // to avoid name collisions
        tuple val(meta),
            path(reads, stageAs: "reads/*"),
            path(index, stageAs: "index/*"),
            path(stats, stageAs: "stats/*")
    output:
        // use sub-dir to avoid name clashes (in the unlikely event of a sample alias
        // being `reads` or `stats`)
        path "out/*"
    script:
    String outdir = "out/${meta["alias"]}"
    String metaJson = new JsonBuilder(meta).toPrettyString()
    String reads = reads.fileName.name == OPTIONAL_FILE.name ? "" : reads
    String index = index.fileName.name == OPTIONAL_FILE.name ? "" : index
    String stats = stats.fileName.name == OPTIONAL_FILE.name ? "" : stats
    """
    mkdir -p $outdir
    echo '$metaJson' > metamap.json
    mv metamap.json $reads $stats $index $outdir
    """
}

// workflow module
workflow pipeline {
    take:
        reads
    main:
        // fastq_ingress doesn't have the index; add one extra null for compatibility.
        // We do not use variable name as assigning variable name with a tuple
        // not matching (e.g. meta, bam, bai, stats <- [meta, bam, stats]) causes
        // the workflow to crash.
        reads = reads
        .map{
            it.size() == 4 ? it : [it[0], it[1], null, it[2]]
        }

        client_fields = params.client_fields && file(params.client_fields).exists() ? file(params.client_fields) : OPTIONAL_FILE
        software_versions = getVersions()
        workflow_params = getParams()

        // get metadata and stats files, keeping them ordered (could do with transpose I suppose)
        reads.multiMap{ meta, path, index, stats ->
            meta: meta
            stats: stats ?: OPTIONAL_FILE
        }.set { for_report }
        metadata = for_report.meta.collect()
        // create a file list of the stats, and signal if its empty or not
        stats = for_report.stats | ifEmpty(OPTIONAL_FILE) | collect | map { [it, it[0] == OPTIONAL_FILE] } 
 
        report = makeReport(
            metadata,
            stats,
            client_fields,
            software_versions,
            workflow_params,
            workflow.manifest.version
        )
        
        // replace `null` with path to optional file
        reads
        | map { 
            meta, path, index, stats ->
            [ meta, path ?: OPTIONAL_FILE, index ?: OPTIONAL_FILE, stats ?: OPTIONAL_FILE ]
        }
        | collectIngressResultsInDir
    emit:
        ingress_results = collectIngressResultsInDir.out
        report
        workflow_params
        // TODO: use something more useful as telemetry
        telemetry = workflow_params
}


// entrypoint workflow
WorkflowMain.initialise(workflow, params, log)
workflow {

    Pinguscript.ping_start(nextflow, workflow, params)

    // demo mutateParam
    if (params.containsKey("mutate_fastq")) {
        CWUtil.mutateParam(params, "fastq", params.mutate_fastq)
    }

    def samples
    if (params.fastq) {
        samples = fastq_ingress([
            "input":params.fastq,
            "sample":params.sample,
            "sample_sheet":params.sample_sheet,
            "analyse_unclassified":params.analyse_unclassified,
            "stats": params.wf.fastcat_stats,
            "fastcat_extra_args": "",
            "required_sample_types": [],
            "watch_path": params.wf.watch_path,
            "fastq_chunk": params.fastq_chunk,
            "per_read_stats": params.wf.per_read_stats,
        ])
    } else {
        // if we didn't get a `--fastq`, there must have been a `--bam` (as is codified
        // by the schema)
        samples = xam_ingress([
            "input":params.bam,
            "sample":params.sample,
            "sample_sheet":params.sample_sheet,
            "analyse_unclassified":params.analyse_unclassified,
            "keep_unaligned": params.wf.keep_unaligned,
            "stats": params.wf.bamstats,
            "watch_path": params.wf.watch_path,
            "return_fastq": params.wf.return_fastq,
            "fastq_chunk": params.fastq_chunk,
            "per_read_stats": params.wf.per_read_stats
        ])
    }

    // group back the possible multiple fastqs from the chunking. In
    // a "real" workflow this wouldn't be done immediately here and
    // we'd do something more interesting first. Note that groupTuple
    // will give us a file list of `[null]` for missing samples, reduce
    // this back to `null`.
    def decorate_samples
    if (params.wf.return_fastq || params.fastq) {
        decorate_samples = samples
            .map {meta, fname, stats ->
                [meta["group_key"], meta, fname, stats]}
            .groupTuple()
            .map { key, metas, fnames, statss ->
                if (fnames[0] == null) {fnames = null}
                // put all the group_indexes into a single list for safe keeping (mainly testing)
                [
                    metas[0] + ["group_index":  metas.collect{it["group_index"]}],
                    fnames, statss[0]]
            }
    } else {
        decorate_samples = samples
    }

    pipeline(decorate_samples)
    pipeline.out.ingress_results
        | map { [it, "${params.fastq ? "fastq" : "xam"}_ingress_results"] }
        | concat (
            pipeline.out.report.concat(pipeline.out.workflow_params)
                | map { [it, null] })
        | output
}

workflow.onComplete {
    Pinguscript.ping_complete(nextflow, workflow, params)
}
workflow.onError {
    Pinguscript.ping_error(nextflow, workflow, params)
}
