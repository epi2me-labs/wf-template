"""Test check_sample_sheet.py."""

import os

import pytest
from workflow_glue import check_sample_sheet


# define a list of error messages (either the complete message or the first couple words
# in case the error message is customized by `check_sample_sheet.py`) and required
# sample types to be tested.
ERROR_MESSAGES = [
    ("sample_sheet_1.csv", "", ""),
    # check required sample types
    ("sample_sheet_1.csv", "Sample sheet requires at least 1 of ", "positive_control"),
    ("sample_sheet_1.csv", "Not an allowed sample type: ", "invalid_sample_type"),
    # check sample sheet structure etc.
    ("sample_sheet_2.csv", "'barcode' column missing", ""),
    ("sample_sheet_3.csv", "'alias' column missing", ""),
    ("sample_sheet_4.csv", "values in 'barcode' column not unique", ""),
    ("sample_sheet_5.csv", "values in 'alias' column not unique", ""),
    ("sample_sheet_6.csv", "Unexpected number of cells in row number 2", ""),
    ("sample_sheet_7.csv", "found unexpected values in 'type' column: ", ""),
    ("sample_sheet_8.csv", "values in 'barcode' column are different lengths", ""),
    ("sample_sheet_9.csv", "values in 'barcode' column are incorrect format", ""),
    # misc
    ("missing.csv", "Could not open sample sheet", ""),
    ("utf8_bom.csv", "", ""),  # check this does not fail
    # check other input formats
    ("sample_sheet_1.csv.zip", "The sample sheet doesn't seem to be a CSV file.", ""),
    ("sample_sheet_1.xlsx", "The sample sheet doesn't seem to be a CSV file.", ""),
    ("sample_sheet_10.csv", "", ""),  # check this does not fail
    (
        "sample_sheet_11.csv",
        "if an 'analysis_group' column exists, it needs values in each row",
        "",
    ),
]


@pytest.fixture
def test_data(request):
    """Define data location fixture."""
    return os.path.join(
        request.config.getoption("--test_data"),
        "workflow_glue",
        "check_sample_sheet")


@pytest.mark.parametrize("sample_sheet_name,error_msg,required_types", ERROR_MESSAGES)
def test_check_sample_sheet(
        capsys, test_data, sample_sheet_name, error_msg, required_types):
    """Test the sample sheets."""
    expected_error_message = error_msg
    sample_sheet_path = f"{test_data}/{sample_sheet_name}"
    args = [sample_sheet_path]
    if required_types:
        args += ['--required_sample_types', required_types]
    parsed_args = check_sample_sheet.argparser().parse_args(args)
    try:
        check_sample_sheet.main(parsed_args)
    except SystemExit:
        pass
    out, _ = capsys.readouterr()
    if expected_error_message == "":
        assert len(out.strip()) == 0
    else:
        assert out.startswith(expected_error_message)
