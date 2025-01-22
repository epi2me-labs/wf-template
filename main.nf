#!/usr/bin/env nextflow

//defining parameters




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

process SEQKIT {
	container 'community.wave.seqera.io/library/seqkit:2.9.0--e0e29e1f5c28842a'

	input:
	path(reads_file) 

	output:
	path("SEQKIT_${sample_id}_logs")

	script:
	"""
	seqkit seq -Q 8 -m 1000 ${reads_file} > ${sample_id}_filtered.fastq -o "SEQKIT_${sample_id}_logs" //{Q} only print sequences with average quality greater or equal than this limit {m} only print sequences longer than or equal to the minimum length
	"""
}


process FILTLONG{
	//filtering long reads
	publishDir params.outdir, mode: 'copy'

	container 'community.wave.seqera.io/library/filtlong:0.2.1--5cb367f8dffa9e28' 

	input:
	path(reads_file)
	
	output:
	path("${reads_file}.fastq.gz")

	script:
	"""
	filtlong --min_length $params.minlength --keep_percent $params.keep_percent --target_bases $params.targetbases ${reads_file} | gzip > ${reads_file}.fastq.gz
	
	cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        filtlong: \$( filtlong --version | sed -e "s/Filtlong v//g" )
    END_VERSIONS
	"""

}





workflow {
	reads=Channel.fromPath(params.input)
	NANOPLOT(reads)

	FILTLONG(reads)
	
}


//notes
//doing Nanoplot before and after filtering 
