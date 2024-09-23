"""Test the reheader_samstream script.

This may seem a bit overkill but it's going to touch a lot of files and
the collision handling could do with a bit of robustness to avoid
trouble later. There are two concerns of the testing here:

    - Ensuring PG collision handling is not garbage
    - Lightly testing the script end to end to accept the output is also
      not going to be garbage
"""
from io import StringIO

import pytest
from workflow_glue.reheader_samstream import argparser, reheader_samstream, SamHeader


def test_resolve_ok_ordered_pg_chain():
    """Test resolution of PG to PP links."""
    records = [
        {"ID": "first"},
        {"ID": "second", "PP": "first"},
        {"ID": "third", "PP": "second"},
    ]
    links = SamHeader.resolve_pg_chain(records)
    assert links == {
        "first": None,
        "second": "first",
        "third": "second",
    }


def test_resolve_ok_unordered_pg_chain():
    """Test resolution of PG to PP links when input is unordered."""
    records = [
        {"ID": "third", "PP": "second"},
        {"ID": "second", "PP": "first"},
        {"ID": "first"},
    ]
    links = SamHeader.resolve_pg_chain(records)
    assert links == {
        "first": None,
        "second": "first",
        "third": "second",
    }


def test_resolve_bad_pg_chain_cycle():
    """Test resolution of PG to PP links explodes when a cycle is present."""
    records = [
        {"ID": "first"},
        {"ID": "third", "PP": "second"},
        {"ID": "second", "PP": "third"},
    ]
    with pytest.raises(Exception, match="PG chain appears to contain cycle: \\['third', 'second', 'third'\\]"):  # noqa:E501
        SamHeader.resolve_pg_chain(records)


def test_resolve_pg_chain_no_head():
    """Test PG chain with no head (ie. no PG has a null PP.ID) yields error."""
    records = [
        {"ID": "first", "PP": "zero"},
        {"ID": "second", "PP": "first"},
        {"ID": "third", "PP": "second"},
    ]
    with pytest.raises(Exception, match="PG chain does not have a head."):
        SamHeader.resolve_pg_chain(records)


def test_resolve_pg_chain_multi_head():
    """Test PG chain with two heads (ie. no PG has a null PP.ID) yields error."""
    records = [
        {"ID": "first", "PP": None},
        {"ID": "second", "PP": None},
        {"ID": "third", "PP": "second"},
    ]
    with pytest.raises(Exception, match="PG chain has multiple heads."):
        SamHeader.resolve_pg_chain(records)


def test_resolve_pg_chain_no_entries():
    """Test PG chain resolution when input is empty does not explode."""
    assert SamHeader.resolve_pg_chain([]) == {}


def test_resolve_pg_chain_duplicate_pp():
    """Test PG chain containing duplicated references to PP does not explode."""
    records = [
        {"ID": "first"},
        {"ID": "second", "PP": "first"},
        {"ID": "third", "PP": "first"},
    ]
    links = SamHeader.resolve_pg_chain(records)
    assert links == {
        "first": None,
        "second": "first",
        "third": "first",
    }


def test_simple_pg_collision():
    """Test PG collision handling correctly uncollides duplicate PG ID."""
    sh = SamHeader()
    sh.add_line("@PG\tID:HOOT")
    pg = sh.add_line("@PG\tID:HOOT")
    assert pg["ID"] == "HOOT-0"
    assert pg["PP"] == "HOOT"
    pg = sh.add_line("@PG\tID:MEOW\tPP:HOOT")
    assert pg["ID"] == "MEOW"
    assert pg["PP"] == "HOOT-0"
    assert sh.last_pgid == "MEOW"


def test_rg_collision_good():
    """Test exact matches of RG records are not duplicated."""
    sh = SamHeader()
    sh.add_line("@RG\tID:HOOT")
    sh.add_line("@RG\tID:HOOT")
    assert len(sh.rg_records) == 1


def test_rg_collision_bad():
    """Test matches of RG record with same ID but different content explodes."""
    sh = SamHeader()
    sh.add_line("@RG\tID:HOOT")
    with pytest.raises(Exception, match="Duplicate RG with ID 'HOOT' conflicts with previously seen RG with same ID."):  # noqa:E501
        sh.add_line("@RG\tID:HOOT\tDS:HELLO")


def test_add_line():
    """Test adding a CO, RG and PG with add_line updates internal structure."""
    sh = SamHeader()
    sh.add_line("@RG\tID:HOOT")
    assert sh.rg_records[0] == {"ID": "HOOT"}
    sh.add_line("@CO\tthis is my comment")
    assert sh.co_records[0] == "this is my comment"
    sh.add_line("@PG\tID:HOOT")
    assert sh.pg_records[0] == {"ID": "HOOT"}


def test_add_line_hd():
    """Test adding an HD overrides the HD."""
    sh = SamHeader()
    test_hd = "@HD\tVN:1.6\tSO:first"
    sh.add_line(test_hd)
    test_hd = "@HD\tVN:1.6\tSO:second"
    sh.add_line(test_hd)
    assert sh.hd == test_hd


def test_add_line_sq():
    """Test adding an SQ updates the structure."""
    sh = SamHeader()
    sh.add_line("@SQ\tSN:MEOW")
    assert len(sh.sq_records) == 1
    assert sh.sq_records[0] == "SN:MEOW"


def test_add_line_garbage():
    """Test adding an SQ updates the structure."""
    sh = SamHeader()
    with pytest.raises(Exception, match="Unknown record type"):
        sh.add_line("@XX\tSN:MEOW")


def test_add_line_reset_sq_hd():
    """Test encountering an SQ after an HD resets the SQ."""
    sh = SamHeader()
    sh.add_line("@SQ\tSN:MEOW")
    assert not sh.reset_sq
    assert len(sh.sq_records) == 1
    sh.add_line("@HD\tVN:1.6\tSO:newhead")
    assert sh.reset_sq
    sh.add_line("@SQ\tSN:HOOT")
    assert not sh.reset_sq
    sh.add_line("@SQ\tSN:HONK")
    assert len(sh.sq_records) == 2


def test_add_line_reset_sq_interleave_sq():
    """Test encountering an SQ after an HD resets the SQ."""
    sh = SamHeader()
    sh.add_line("@SQ\tSN:HOOT")
    sh.add_line("@SQ\tSN:MEOW")
    assert not sh.reset_sq
    assert len(sh.sq_records) == 2
    sh.add_line("@PG\tID:program")
    assert sh.reset_sq
    sh.add_line("@SQ\tSN:HISS")
    assert not sh.reset_sq
    sh.add_line("@SQ\tSN:HONK")
    assert len(sh.sq_records) == 2


def test_add_pg_line_premature_ppid():
    """Test PP.ID before PG.ID explodes."""
    sh = SamHeader()
    with pytest.raises(Exception, match="Encountered PG.PP 'MEOW' before observing corresponding PG.ID"):  # noqa:E501
        sh.add_line("@PG\tID:HOOT\tPP:MEOW")


def test_dict_from_pg_good():
    """Test PG struct is created from string."""
    pg_fields = [
        "@PG",
        "ID:HOOT",
        "PN:hoot call",
        "CL:hoot --call me maybe",
        "PP:MEOW",
        "DS:this was a hoot",
        "VN:8",
    ]
    assert SamHeader.str_to_record('\t'.join(pg_fields)) == ("@PG", {
        "ID": "HOOT",
        "PN": "hoot call",
        "CL": "hoot --call me maybe",
        "PP": "MEOW",
        "DS": "this was a hoot",
        "VN": "8",
    })


def test_str_to_record_malformed():
    """Test malformed struct explodes."""
    with pytest.raises(Exception, match="Record type could not be determined:"):
        assert SamHeader.str_to_record("@PG\\tID:HOOT\\tPN:hoot call\\tCL:hoot --call me maybe\\tPP:MEOW\\tDS:this was a hoot\\tVN:8")  # noqa:E501


def test_str_to_record_type_malformed():
    """Test malformed struct explodes."""
    with pytest.raises(Exception, match="Record type malformed:"):
        assert SamHeader.str_to_record("@PG:ID:HOOT\tPN:hoot call\tCL:hoot --call me maybe\tPP:MEOW\tDS:this was a hoot\tVN:8")  # noqa:E501


def test_dict_from_pg_bad_key():
    """Test PG record with bad key explodes."""
    with pytest.raises(Exception, match="PG with bad key 'OHNO'"):
        SamHeader.str_to_record("@PG\tID:HOOT\tOHNO:MEOW")


def test_dict_from_pg_no_id():
    """Test PG record with missing ID key explodes."""
    with pytest.raises(Exception, match="PG with no ID: PN:HOOT\tVN:8"):
        SamHeader.str_to_record("@PG\tPN:HOOT\tVN:8")


def test_write_header():
    """Test add_line to write_header circuit."""
    sh = SamHeader()
    sh.add_line("@RG\tID:HOOT")
    sh.add_line("@CO\tthis is my comment")
    sh.add_line("@PG\tID:HOOT")
    sh.add_line("@PG\tID:HOOT")

    output = StringIO()
    sh.write_header(output)
    assert output.getvalue() == """@HD\tVN:1.6\tSO:unknown
@RG\tID:HOOT
@PG\tID:HOOT
@PG\tID:HOOT-0\tPP:HOOT
@CO\tthis is my comment
"""


def test_e2e_blank():
    """Run main with no input to ensure valid empty output with HD is created."""
    args = argparser().parse_args([
        "/dev/null",
    ])
    header_in = StringIO()  # no input header
    stream_in = StringIO()  # no input stream
    stream_out = StringIO()
    reheader_samstream(header_in, stream_in, stream_out, args)
    assert stream_out.getvalue() == "@HD\tVN:1.6\tSO:unknown\n"


def test_e2e_write_header_with_no_alignments():
    """Run main with no reads to ensure header is still written when header is EOF."""
    args = argparser().parse_args([
        "/dev/null",
    ])
    header_in = StringIO("@RG\tID:hoot\n")
    stream_in = StringIO("@PG\tID:hoot\n")
    stream_out = StringIO()
    reheader_samstream(header_in, stream_in, stream_out, args)
    assert stream_out.getvalue() == """@HD\tVN:1.6\tSO:unknown
@RG\tID:hoot
@PG\tID:hoot
"""


def test_e2e_write_header_with_stream_hd_sq():
    """Run main and ensure HD from stream is overriden from default and SQ are used."""
    args = argparser().parse_args([
        "/dev/null",
    ])
    header_in = StringIO("@RG\tID:hoot\n")
    stream_in = StringIO("@HD\tVN:1.6\tSO:sorted\n@SQ\tSN:my-seq\tLN:8000\n")
    stream_out = StringIO()
    reheader_samstream(header_in, stream_in, stream_out, args)
    assert stream_out.getvalue() == """@HD\tVN:1.6\tSO:sorted
@SQ\tSN:my-seq\tLN:8000
@RG\tID:hoot
"""


def test_e2e():
    """Run main with simple insert arg, input and stream header and check result."""
    args = argparser().parse_args([
        "/dev/null",
        "--insert",
        "@PG\tID:inserted_rg\tPN:hoot-tools\tVN:8",
        "--insert",
        "@PG\tID:inserted_rg2\tPN:hoot-tools-again\tVN:2",
    ])
    header_in = StringIO("@RG\tID:my_reads\n@SQ\tSN:this-should-not-appear\tLN:100\n")
    stream_in = StringIO('\n'.join([
        "@HD\tVN:1.6\tSO:hooted",
        "@SQ\tSN:this-should-appear\tLN:1000",
        "@SQ\tSN:this-should-also-appear\tLN:5000",
        "@PG\tID:my_program",
        "@PG\tID:my_other_program",
        "READ1",
        "READ2",
        "READ3",
        "READ4",
    ]) + '\n')
    stream_out = StringIO()
    reheader_samstream(header_in, stream_in, stream_out, args)
    assert stream_out.getvalue() == """@HD\tVN:1.6\tSO:hooted
@SQ\tSN:this-should-appear\tLN:1000
@SQ\tSN:this-should-also-appear\tLN:5000
@RG\tID:my_reads
@PG\tID:inserted_rg\tPN:hoot-tools\tVN:8
@PG\tID:inserted_rg2\tPN:hoot-tools-again\tVN:2\tPP:inserted_rg
@PG\tID:my_program\tPP:inserted_rg2
@PG\tID:my_other_program\tPP:my_program
READ1
READ2
READ3
READ4
"""


def test_e2e_bad_insert():
    """Run main with bad insert arg explodes."""
    args = argparser().parse_args([
        "/dev/null",
        "--insert",
        "@PG\\tID:inserted_rg\\tPN:hoot-tools\\tVN:8",
    ])
    header_in = StringIO("@RG\tID:my_reads\n")
    stream_in = StringIO('\n'.join([
        "READ1",
    ]) + '\n')
    stream_out = StringIO()
    with pytest.raises(Exception, match="Record type could not be determined"):
        reheader_samstream(header_in, stream_in, stream_out, args)


def test_e2e_no_hd_like_minimap2():
    """Run main with simple insert arg, input and stream header and check result."""
    args = argparser().parse_args([
        "/dev/null",
        "--insert",
        "@PG\tID:inserted_rg\tPN:hoot-tools\tVN:8",
        "--insert",
        "@PG\tID:inserted_rg2\tPN:hoot-tools-again\tVN:2",
    ])
    header_in = StringIO("@RG\tID:my_reads\n@SQ\tSN:this-should-not-appear\tLN:100\n")
    stream_in = StringIO('\n'.join([
        "@SQ\tSN:this-should-appear\tLN:1000",
        "@SQ\tSN:this-should-also-appear\tLN:5000",
        "@PG\tID:my_program",
        "@PG\tID:my_other_program",
        "READ1",
        "READ2",
        "READ3",
        "READ4",
    ]) + '\n')
    stream_out = StringIO()
    reheader_samstream(header_in, stream_in, stream_out, args)
    assert stream_out.getvalue() == """@HD\tVN:1.6\tSO:unknown
@SQ\tSN:this-should-appear\tLN:1000
@SQ\tSN:this-should-also-appear\tLN:5000
@RG\tID:my_reads
@PG\tID:inserted_rg\tPN:hoot-tools\tVN:8
@PG\tID:inserted_rg2\tPN:hoot-tools-again\tVN:2\tPP:inserted_rg
@PG\tID:my_program\tPP:inserted_rg2
@PG\tID:my_other_program\tPP:my_program
READ1
READ2
READ3
READ4
"""
