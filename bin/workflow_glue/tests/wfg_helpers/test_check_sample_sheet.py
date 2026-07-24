"""Test check_sample_sheet.py."""

import json
import os

import pytest
from workflow_glue.wfg_helpers import check_sample_sheet
from workflow_glue.wfg_helpers.validators.default import SampleSheetValidator


@pytest.fixture
def test_data(request):
    """Define data location fixture."""
    return os.path.join(
        request.config.getoption("--test_data"),
        "workflow_glue",
        "check_sample_sheet")


def test_load_validator_modules_discovers_package_modules():
    """Test that all modules in the validators package are discovered."""
    module_names = {
        mod.__name__
        for mod in check_sample_sheet.load_validator_modules()
    }

    assert "workflow_glue.wfg_helpers.validators.default" in module_names


def test_log_error_adds_context_when_provided():
    """Test that validator errors can include column and line context."""
    validator = SampleSheetValidator({})

    validator.log_error("Invalid value", column="barcode", lineno=2)
    validator.log_error("Missing value", column="alias")
    validator.log_error("Unexpected cells", lineno=4)

    assert validator.errors == [
        "Invalid value (column: barcode, line: 2)",
        "Missing value (column: alias)",
        "Unexpected cells (line: 4)",
    ]


def test_alias_field_uses_expected_name_for_options():
    """Test that alias_field changes with no_barcode in options."""
    assert SampleSheetValidator({}).alias_field == "alias"
    assert SampleSheetValidator({}, {"no_barcode": True}).alias_field == "sample_name"


def test_load_validators_passes_options_to_validators():
    """Test that validators receive the shared options dict."""
    validator_classes = check_sample_sheet.load_validators(
        check_sample_sheet.load_validator_modules(),
        {},
        options={"no_barcode": True},
    )

    assert validator_classes
    assert all(v.options.get("no_barcode") for v in validator_classes)
    assert all(v.alias_field == "sample_name" for v in validator_classes)


# Define test parameters
PARAMS = [
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_1.csv",
            "error_msg": "",
            "wf_params": {},
        },
        id="ss1_ok",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_1.csv",
            "error_msg": "Sample sheet requires at least 1 of ",
            "wf_params": {"required_sample_types": ["positive_control"]},
        },
        id="ss1_missing_required_positive_control",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_1.csv",
            "error_msg": "Not an allowed sample type: ",
            "wf_params": {"required_sample_types": "invalid_sample_type"},
        },
        id="ss1_invalid_required_type",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_2.csv",
            "error_msg": "Column missing (column: barcode)",
            "wf_params": {},
        },
        id="ss2_missing_barcode",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_3.csv",
            "error_msg": "Column missing (column: alias)",
            "wf_params": {},
        },
        id="ss3_missing_alias",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_4.csv",
            "error_msg": (
                "Value not unique: barcode01 (column: barcode, line: 2)"
            ),
            "wf_params": {},
        },
        id="ss4_barcode_not_unique",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_5.csv",
            "error_msg": (
                "Value not unique: patient_id_5 (column: alias, line: 2)"
            ),
            "wf_params": {},
        },
        id="ss5_alias_not_unique",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_6.csv",
            "error_msg": "Unexpected number of cells in row (line: 1)",
            "wf_params": {},

        },
        id="ss6_unexpected_cells_row2",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_7.csv",
            "error_msg": (
                "Unexpected value: unexpected_type_value "
                "(column: type, line: 1)"
            ),
            "wf_params": {},
        },
        id="ss7_unexpected_type_values",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_8.csv",
            "error_msg": (
                "Values are different lengths: barcode02 "
                "(column: barcode, line: 2)"
            ),
            "wf_params": {},
        },
        id="ss8_barcode_length_mismatch",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_9.csv",
            "error_msg": (
                "Value has incorrect format: arcode05 "
                "(column: barcode, line: 5)"
            ),
            "wf_params": {},
        },
        id="ss9_barcode_format",
    ),
    pytest.param(
        {
            "sample_sheet_name": "missing.csv",
            "error_msg": "Could not open sample sheet",
            "wf_params": {}
        },
        id="missing_file",
    ),
    pytest.param(
        {
            "sample_sheet_name": "utf8_bom.csv",
            "error_msg": "",
            "wf_params": {},
        },
        id="utf8_bom_ok",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_1.csv.zip",
            "error_msg": "The sample sheet doesn't seem to be a CSV file.",
            "wf_params": {},
        },
        id="ss1_zip_not_csv",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_1.xlsx",
            "error_msg": "The sample sheet doesn't seem to be a CSV file.",
            "wf_params": {}
        },
        id="ss1_xlsx_not_csv",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_10.csv",
            "error_msg": "",
            "wf_params": {}
        },
        id="ss10_barcode_alias_type_only_ok",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_11.csv",
            "error_msg": (
                "Column exists but needs values in each row "
                "(column: analysis_group, line: 8)"
            ),
            "wf_params": {},
        },
        id="ss11_analysis_group_missing_values",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_12.csv",
            "error_msg": (
                "Value must not begin with 'barcode': barcode01 "
                "(column: alias, line: 1)"
            ),
            "wf_params": {},
        },
        id="ss12_alias_start_barcode",
    ),
]


NO_BARCODE_PARAMS = [
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_13.csv",
            "error_msg": (
                "Column missing (column: sample_name)\n"
                "Column must not be present with --no_barcode (column: alias)"
            ),
            "wf_params": {},
        },
        id="ss13_alias_present_with_no_barcode",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_14.csv",
            "error_msg": "",
            "wf_params": {},
        },
        id="ss14_no_barcode_ok",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_15.csv",
            "error_msg": (
                "Column must not be present with --no_barcode (column: alias)"
            ),
            "wf_params": {},
        },
        id="ss15_alias_present_with_no_barcode",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_16.csv",
            "error_msg": (
                "Column must not be present with --no_barcode (column: barcode)"
            ),
            "wf_params": {},
        },
        id="ss16_barcode_present_with_no_barcode",
    ),
    pytest.param(
        {
            "sample_sheet_name": "sample_sheet_17.csv",
            "error_msg": "Column missing (column: sample_name)",
            "wf_params": {},
        },
        id="ss17_sample_name_missing_with_no_barcode",
    ),
]


ALL_PARAMS = [
    pytest.param(param.values[0], False, id=param.id)
    for param in PARAMS
] + [
    pytest.param(param.values[0], True, id=param.id)
    for param in NO_BARCODE_PARAMS
]


@pytest.mark.parametrize("params,no_barcode", ALL_PARAMS)
def test_check_sample_sheet(
        tmp_path, capsys, test_data, params, no_barcode):
    """Test the sample sheets."""
    expected_error_message = params['error_msg']
    sample_sheet_path = f"{test_data}/{params['sample_sheet_name']}"

    params_json = str(tmp_path / 'params.json')
    with open(params_json, 'w') as f:
        json.dump(params['wf_params'], f)

    args = [sample_sheet_path, params_json]
    if no_barcode:
        args.append("--no_barcode")

    parsed_args = check_sample_sheet.argparser().parse_args(args)

    try:
        check_sample_sheet.main(parsed_args)
    except SystemExit:
        pass

    out, _ = capsys.readouterr()

    if expected_error_message == "":
        assert len(out.strip()) == 0
    else:
        assert expected_error_message in out


def _run_check_sample_sheet(
        sample_sheet_path, params_json, capsys):
    args = [str(sample_sheet_path), str(params_json)]
    parsed_args = check_sample_sheet.argparser().parse_args(args)

    try:
        check_sample_sheet.main(parsed_args)
    except SystemExit:
        pass

    out, _ = capsys.readouterr()
    return out


def test_reject_missing_alias_column(tmp_path, capsys):
    """Missing alias column should fail through ingress validation."""
    sample_sheet_path = tmp_path / "sample_sheet_missing_alias.csv"
    sample_sheet_path.write_text(
        "barcode,condition\n"
        "barcode01,control\n"
    )

    params_json = tmp_path / "params.json"
    params_json.write_text("{}")

    out = _run_check_sample_sheet(sample_sheet_path, params_json, capsys)

    assert out.startswith("Column missing (column: alias)")


def test_sane_alias_values(tmp_path, capsys):
    """Alias values matching AliasRules should validate cleanly."""
    sample_sheet_path = tmp_path / "sample_sheet.csv"
    sample_sheet_path.write_text(
        "barcode,alias,condition\n"
        "barcode01,sample-1,control\n"
        "barcode02,sample_1,control\n"
        "barcode03,1sample,treated\n"
        "barcode04,01,treated\n"  # numeric
        "barcode05,sample.1,treated\n"
        "barcode06,1.sample,treated\n"
    )

    params_json = tmp_path / "params.json"
    params_json.write_text("{}")

    out = _run_check_sample_sheet(
        sample_sheet_path, params_json, capsys
    )

    assert out == ""


def test_reject_insane_alias(tmp_path, capsys):
    """Aliases with invalid characters or invalid starting characters fail."""
    sample_sheet_path = tmp_path / "sample_sheet.csv"
    sample_sheet_path.write_text(
        "barcode,alias,condition\n"
        "barcode01,sample 1,control\n"
        "barcode02,sample#1,control\n"
        "barcode03,sample?1,treated\n"
        "barcode04,sample$1,treated\n"
        "barcode05,café,treated\n"
        "barcode06,Grüße,treated\n"
        "barcode07,.sample,treated\n"
        "barcode08,_sample,treated\n"
        "barcode09,,treated\n"  # empty
    )

    params_json = tmp_path / "params.json"
    params_json.write_text("{}")

    out = _run_check_sample_sheet(
        sample_sheet_path, params_json, capsys
    )

    assert out.startswith(
        "Invalid value sample 1. Allowed values start with letters or numbers "
        "and may contain only letters, numbers, '.', '_' or '-' "
        "(column: alias, line: 1)"
    )
    assert "Invalid value sample#1" in out
    assert "Invalid value sample?1." in out
    assert "Invalid value sample$1." in out
    assert "Invalid value café." in out
    assert "Invalid value Grüße." in out
    assert "Invalid value .sample." in out
    assert "Invalid value _sample." in out
    assert "Empty alias" in out


def test_reject_duplicate_aliases(
        tmp_path, capsys):
    """Duplicate aliases should fail through ingress validation."""
    sample_sheet_path = tmp_path / "sample_sheet_duplicate_alias.csv"
    sample_sheet_path.write_text(
        "barcode,alias,condition\n"
        "barcode01,rep1,control\n"
        "barcode02,rep1,control\n"
    )

    params_json = tmp_path / "params.json"
    params_json.write_text("{}")

    args = [str(sample_sheet_path), str(params_json)]
    parsed_args = check_sample_sheet.argparser().parse_args(args)

    try:
        check_sample_sheet.main(parsed_args)
    except SystemExit:
        pass

    out, _ = capsys.readouterr()

    assert out.startswith("Value not unique: rep1 (column: alias, line: 2)")
