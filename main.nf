#!/usr/bin/env nextflow

process NANOPLOT {
	publishDir params.outdir, mode: 'copy'

	container 'community.wave.seqera.io/library/nanoplot:1.43.0--c7226d331b0968bf'

	input:
	path(reads_file)
	//ONT file and meta:map



	output:
	path("nanoplot_logs")
	//.html (report), .png (plots), .txt(Stats from Nanoplot), .log, .yml (containing software versions)
	
	script:
	"""
	mkdir nanoplot_logs
	NanoPlot --fastq ${reads_file} --outdir nanoplot_logs --threads 4 --loglength

	cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        nanoplot: \$(echo \$(NanoPlot --version 2>&1) | sed 's/^.*NanoPlot //; s/ .*\$//')
    END_VERSIONS
	"""
}

workflow {
	reads=Channel.fromPath(params.input)
	NANOPLOT(reads)
	
}
