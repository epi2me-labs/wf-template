"""Test the configure_igv script."""

import json

import pytest
from workflow_glue.wfg_helpers.configure_igv import main


DEFAULT_ALN_IN = {
    "displayMode": "SQUISHED",
    "colorBy": "strand",
}

NO_SAMPLE_FOFN = """reference.fasta
reference.fasta.fai
sampleB.bam
sampleB.bam.bai
sampleA.bam
sampleA.bam.bai"""

NO_SAMPLE_EXPECTED_IGV_OUT = {
    "reference": {
        "id": "ref",
        "name": "ref",
        "wholeGenomeView": False,
        "fastaURL": "reference.fasta",
        "indexURL": "reference.fasta.fai",
    },
    "tracks": [
        {
            "name": "sampleB.bam",
            "type": "alignment",
            "format": "bam",
            "url": "sampleB.bam",
            "indexURL": "sampleB.bam.bai",
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
        {
            "name": "sampleA.bam",
            "type": "alignment",
            "format": "bam",
            "url": "sampleA.bam",
            "indexURL": "sampleA.bam.bai",
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
    ],
}

WF_AMPLICON_FOFN = """reference.fasta
reference.fasta.fai
sample B,sampleB.bam
sample B,sampleB.bam.bai
sample B variant,medaka.annotated.vcf.gz
sample A,sampleA.bam
sample A,sampleA.bam.bai
sample A variant,medaka.annotated.vcf.gz"""

WF_AMPLICON_EXPECTED_IGV_OUT = {
    "reference": {
        "id": "ref",
        "name": "ref",
        "wholeGenomeView": False,
        "fastaURL": "reference.fasta",
        "indexURL": "reference.fasta.fai",
    },
    "tracks": [
        {
            "name": "sample A: sampleA.bam",
            "type": "alignment",
            "format": "bam",
            "url": "sampleA.bam",
            "indexURL": "sampleA.bam.bai",
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
        {
            "name": "sample A variant: medaka.annotated.vcf.gz",
            "type": "variant",
            "format": "vcf",
            "url": "medaka.annotated.vcf.gz",
        },
        {
            "name": "sample B: sampleB.bam",
            "type": "alignment",
            "format": "bam",
            "url": "sampleB.bam",
            "indexURL": "sampleB.bam.bai",
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
        {
            "name": "sample B variant: medaka.annotated.vcf.gz",
            "type": "variant",
            "format": "vcf",
            "url": "medaka.annotated.vcf.gz",
        },
    ],
}

WF_AVA_FOFN = """references/reference.fasta.gz
references/reference.fasta.gz.fai
references/reference.fasta.gz.gzi
sample B,normal/sampleB.bam
sample B,normal/sampleB.bam.bai
sample B custom,custom/sampleBcustom.bam
sample B custom,custom/sampleBcustom.bam.bai
sample A,normal/sampleA.bam
sample A,normal/sampleA.bam.bai
sample A custom,custom/sampleAcustom.bam
sample A custom,custom/sampleAcustom.bam.bai"""

WF_AVA_ALN_IN = [
    {
        "sample A": {
            "displayMode": "SQUISHED",
        },
        "sample A custom": {
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
    },
    {
        "sample B": {
            "displayMode": "SQUISHED",
        },
        "sample B custom": {
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
    },
]

WF_AVA_EXPECTED_IGV_OUT = {
    "reference": {
        "id": "ref",
        "name": "ref",
        "wholeGenomeView": False,
        "fastaURL": "references/reference.fasta.gz",
        "indexURL": "references/reference.fasta.gz.fai",
        "compressedIndexURL": "references/reference.fasta.gz.gzi",
    },
    "tracks": [
        {
            "name": "sample B: sampleB.bam",
            "type": "alignment",
            "format": "bam",
            "url": "normal/sampleB.bam",
            "indexURL": "normal/sampleB.bam.bai",
            "displayMode": "SQUISHED",
        },
        {
            "name": "sample B custom: sampleBcustom.bam",
            "type": "alignment",
            "format": "bam",
            "url": "custom/sampleBcustom.bam",
            "indexURL": "custom/sampleBcustom.bam.bai",
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
        {
            "name": "sample A: sampleA.bam",
            "type": "alignment",
            "format": "bam",
            "url": "normal/sampleA.bam",
            "indexURL": "normal/sampleA.bam.bai",
            "displayMode": "SQUISHED",
        },
        {
            "name": "sample A custom: sampleAcustom.bam",
            "type": "alignment",
            "format": "bam",
            "url": "custom/sampleAcustom.bam",
            "indexURL": "custom/sampleAcustom.bam.bai",
            "displayMode": "SQUISHED",
            "colorBy": "strand",
        },
    ],
}


# IGV wf-ava approach
@pytest.mark.parametrize(
    ("filenames_content,aln,igv_json_expected,keep_order"),
    [
        # wf-alignment (no sample)
        # No sample name is provided, directly the file
        (
            NO_SAMPLE_FOFN,
            DEFAULT_ALN_IN,
            NO_SAMPLE_EXPECTED_IGV_OUT,
            True,
        ),
        # wf-amplicon case
        (
            WF_AMPLICON_FOFN,
            DEFAULT_ALN_IN,
            WF_AMPLICON_EXPECTED_IGV_OUT,
            False
        ),
        # wf-ava case
        (
            WF_AVA_FOFN,
            WF_AVA_ALN_IN,
            WF_AVA_EXPECTED_IGV_OUT,
            True,
        ),
    ],
)
def test_igv_samples_custom_features(
    filenames_content, aln, igv_json_expected, keep_order, tmp_path, capsys
):
    """Test igv JSON file for sample with custom tracks."""
    with open(tmp_path/"file-names.txt", "w") as text_file:
        text_file.write(filenames_content)
    with open(tmp_path/"extra-aln-opts.json", "w") as aln_opts:
        json.dump(aln, aln_opts)
    with open(tmp_path/"igv.json", "w") as igv:
        json.dump(igv_json_expected, igv)

    class Args:
        fofn = tmp_path / "file-names.txt"
        keep_track_order = keep_order
        extra_alignment_opts = tmp_path/"extra-aln-opts.json"
        extra_variant_opts = None
        extra_interval_opts = None
        locus = None
    args = Args()

    main(args)
    captured = capsys.readouterr()
    captured_json = json.loads(captured.out)
    with open(tmp_path/"igv.json", 'r') as output_igv:
        expected_igv = json.loads(output_igv.read())
    assert captured_json.items() == expected_igv.items()
