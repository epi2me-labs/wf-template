"""Test the check bam headers in dir script."""
from array import array
from pathlib import Path
from unittest.mock import Mock

import pysam
import pytest
from workflow_glue.wfg_helpers.check_bam_headers_in_dir import (
    check_header,
    check_n_reads,
    compare_ref_lengths,
    main,
)


@pytest.fixture
def test_data(request):
    """Define test_data location fixture."""
    return Path(request.config.getoption("--test_data"))


@pytest.fixture
def bam_dir(test_data):
    """Get BAM test directory."""
    return test_data / "workflow_glue" / "check_bam_headers"


@pytest.fixture
def ref_file(bam_dir):
    """Get reference file path."""
    return bam_dir / "reference.subseq.fa"


@pytest.fixture
def ref_idx(bam_dir):
    """Get reference index file path."""
    return bam_dir / "reference.subseq.fa.fai"


def make_aligned_segment(name, cigartuples, tags=None):
    """Create a minimal mapped pysam alignment segment."""
    query_length = sum(
        length for op, length in cigartuples
        if op in {0, 1, 4, 7, 8}
    )
    alignment = pysam.AlignedSegment()
    alignment.query_name = name
    alignment.query_sequence = "A" * query_length
    alignment.flag = 0
    alignment.reference_id = 0
    alignment.reference_start = 10
    alignment.mapping_quality = 60
    alignment.cigartuples = cigartuples
    alignment.query_qualities = pysam.qualitystring_to_array("I" * query_length)
    for tag, value in tags or []:
        alignment.set_tag(tag, value)
    return alignment


def write_bam(path, alignments):
    """Write alignments to a tiny real BAM file."""
    header = {
        "HD": {"VN": "1.6", "SO": "coordinate"},
        "SQ": [{"SN": "chr1", "LN": 1000}],
    }
    with pysam.AlignmentFile(path, "wb", header=header) as bam:
        for alignment in alignments:
            bam.write(alignment)


@pytest.mark.parametrize(
    (
        "xam_file, check_ref, expected_sqlines, expected_hdlines, "
        "expected_xam_reflen"
    ),
    [
        # sorted BAM without reference check
        (
            "aligned_sorted/aligned.sorted.bam",
            False,
            [{"LN": 101224, "M5": "9a9a00302ec493d7afb07b89ea2fec8c",
              "SN": "lmonocytogenes"}],
            {"SO": "coordinate", "VN": "1.6"},
            None,
        ),
        # sorted BAM with reference check
        (
            "aligned_sorted/aligned.sorted.bam",
            True,
            [{"LN": 101224, "M5": "9a9a00302ec493d7afb07b89ea2fec8c",
              "SN": "lmonocytogenes"}],
            {"SO": "coordinate", "VN": "1.6"},
            {("lmonocytogenes", 101224)},
        ),
        # unsorted BAM without reference check
        (
            "aligned_unsorted/aligned.unsorted.bam",
            False,
            [{"SN": "lmonocytogenes", "LN": 101224, "M5": None}],
            {"VN": "1.6", "SO": "unsorted", "GO": "query"},
            None,
        )
    ]
)
def test_check_header(
    xam_file, check_ref, expected_sqlines,
    expected_hdlines, expected_xam_reflen, bam_dir
):
    """Test check_header extracts header facts from an open XAM file."""
    full_xam_path = str(bam_dir / xam_file)
    with pysam.AlignmentFile(full_xam_path, check_sq=False) as alignment_file:
        sq_lines, hd_lines, xam_reflen = check_header(
            alignment_file,
            check_ref=check_ref,
        )

    assert sq_lines == expected_sqlines
    assert hd_lines == expected_hdlines
    assert xam_reflen == expected_xam_reflen


def test_check_n_reads_respects_scan_limit(tmp_path):
    """Read scanning should only inspect the configured number of records."""
    bam_path = tmp_path / "reads.bam"
    write_bam(
        bam_path,
        [
            make_aligned_segment("plain", [(0, 10)]),
            make_aligned_segment("splice", [(0, 5), (3, 20), (0, 5)]),
        ],
    )
    with pysam.AlignmentFile(bam_path, check_sq=False) as alignment_file:
        read_facts = check_n_reads(
            alignment_file,
            check_splice_cigars=True,
            read_scan_limit=1,
        )

    assert read_facts["has_reads"]
    assert not read_facts["has_splice_cigars"]
    assert "has_modbase_tags" not in read_facts


def test_main_detects_splice_cigars_in_generated_bam(tmp_path, capsys):
    """Main should emit splice-CIGAR evidence from a real BAM file."""
    write_bam(
        tmp_path / "reads.bam",
        [make_aligned_segment("splice", [(0, 10), (3, 20), (0, 10)])],
    )

    main(Mock(input_path=tmp_path, ref=None, ref_idx=None))
    captured = capsys.readouterr()

    assert "HAS_READS=1" in captured.out
    assert "HAS_SPLICE_CIGARS=1" in captured.out
    assert "HAS_MODBASE_TAGS=0" in captured.out


def test_main_detects_modbase_tags_in_generated_bam(tmp_path, capsys):
    """Main should emit modified-base tag evidence from a real BAM file."""
    write_bam(
        tmp_path / "reads.bam",
        [
            make_aligned_segment(
                "modbase",
                [(0, 10)],
                tags=[
                    ("MM", "A+a,0;"),
                    ("ML", array("B", [200])),
                ],
            ),
        ],
    )

    main(Mock(input_path=tmp_path, ref=None, ref_idx=None))
    captured = capsys.readouterr()

    assert "HAS_READS=1" in captured.out
    assert "HAS_SPLICE_CIGARS=0" in captured.out
    assert "HAS_MODBASE_TAGS=1" in captured.out


@pytest.mark.parametrize(
    "xam_reflen, ref_reflen, expected_result", [
        # single reference match
        ({("lmonocytogenes", 101224)}, {("lmonocytogenes", 101224)}, True),
        # multiple references match
        ({("chr1", 1000), ("chr2", 2000)}, {("chr1", 1000), ("chr2", 2000)}, True),
        # single reference length mismatch
        ({("lmonocytogenes", 101224)}, {("lmonocytogenes", 50000)}, False),
        # multiple references length mismatch
        ({("chr1", 1000), ("chr2", 2000)}, {("chr1", 1000), ("chr2", 3000)}, False),
        # xam is subset of ref
        ({("chr1", 1000)}, {("chr1", 1000), ("chr2", 2000)}, False),
        # ref is subset of xam
        ({("chr1", 1000), ("chr2", 2000)}, {("chr1", 1000)}, False),
        # both empty
        (set(), set(), True),
    ]
)
def test_compare_ref_lengths(xam_reflen, ref_reflen, expected_result):
    """Test compare_ref_lengths function."""
    logger = Mock()
    result = compare_ref_lengths(xam_reflen, ref_reflen, logger)
    assert result == expected_result


@pytest.mark.parametrize(
    (
        "path, expected_unaligned, expected_mixed_sq_headers, "
        "expected_sorted, expected_has_reads, expected_has_splice_cigars, "
        "expected_has_modbase_tags"
    ),
    [
        (
            "aligned_multiple",
            "IS_UNALIGNED=0",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=1",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "aligned_unsorted",
            "IS_UNALIGNED=0",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=0",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "aligned_sorted",
            "IS_UNALIGNED=0",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=1",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "aligned_wrong_ref",
            "IS_UNALIGNED=1",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=1",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "corrupt",
            "IS_UNALIGNED=1",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=0",
            "HAS_READS=0",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "mixed_headers",
            "IS_UNALIGNED=0",
            "MIXED_SQ_HEADERS=1",
            "IS_SORTED=1",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "unaligned",
            "IS_UNALIGNED=1",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=0",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        ),
        (
            "unaligned_multiple",
            "IS_UNALIGNED=1",
            "MIXED_SQ_HEADERS=0",
            "IS_SORTED=0",
            "HAS_READS=1",
            "HAS_SPLICE_CIGARS=0",
            "HAS_MODBASE_TAGS=0",
        )
    ]
)
def test_main(
    path, expected_unaligned, expected_mixed_sq_headers,
    expected_sorted, expected_has_reads, expected_has_splice_cigars,
    expected_has_modbase_tags,
    capsys, bam_dir, ref_file, ref_idx
):
    """Test main sets env variables correctly."""
    full_path = bam_dir / path
    args = Mock(
        input_path=full_path, ref=ref_file, ref_idx=ref_idx)
    main(args)
    captured = capsys.readouterr()
    assert expected_unaligned in captured.out
    assert expected_mixed_sq_headers in captured.out
    assert expected_sorted in captured.out
    assert expected_has_reads in captured.out
    assert expected_has_splice_cigars in captured.out
    assert expected_has_modbase_tags in captured.out
