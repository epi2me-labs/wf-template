"""Test the results_schema and results_schema_helper scripts."""
from dataclasses import dataclass, field

import pytest
from workflow_glue.models.common import Sample, SampleType
from workflow_glue.models.common import WorkflowBaseModel
from workflow_glue.models.common import WorkflowResult
from workflow_glue.models.custom import CheckResult


@pytest.fixture
def test_data(request):
    """Define test_data location fixture."""
    return request.config.getoption("--test_data")


def test_enum_comparisons():
    """Test enum comparison."""
    dummy = SampleType("test_sample")
    # Correct model comparison
    assert dummy == SampleType.test_sample
    # Old method still valid
    assert dummy == "test_sample"
    # String comparisons still work but not advised
    assert dummy.friendly_name() == "Test sample"


def test_model_extension():
    """Test model extension."""
    check = CheckResult(
        check_category="example_check",
        check_name="test",
        check_pass=True,
        check_threshold=None)

    assert check.friendly_check_category() == "Example check category"


@dataclass
class Mass(WorkflowBaseModel):
    """Molecular mass statistics."""

    mass_all: float = field(  # noqa: NT001
        metadata={
            "title": "Molecular mass of all molecules",
            "description": "The total mass of all molecules",
            "unit": "ng"
        })
    mass_ratio: float | None = field(  # noqa: NT001
        default=None,
        metadata={
            "title": "Mass ratio",
            "description": """The ratio of the molecular mass of
            molecules within the user specified read length bounds,
            to the mass of all molecules"""
        })
    mass_full_length: float | None = field(  # noqa: NT001
        default=None,
        metadata={
            "title": "Molecular mass of full length molecules",
            "description": """The total mass of molecules within
            user specified read length bounds"""
        })
    no_title: int | None = field(  # noqa: NT001
        default=None,
        metadata={
            "description": """The total mass of molecules within
            user specified read length bounds"""
        })


@pytest.fixture
def mass():
    """Fixture that returns a Mass instance."""
    return Mass(mass_all=10, mass_ratio=0.493, mass_full_length=5, no_title=444)


def test_get_reportable_tuple(mass):
    """Test to show (title,value) are displayed when requested."""
    assert mass.get("mass_all") == (
        "Molecular mass of all molecules",
        "10 ng",
    )
    assert mass.get("mass_ratio", decimal_places=2) == (
        "Mass ratio",
        "0.49",
    )
    assert mass.get("mass_ratio", decimal_places=2, title=False) == "0.49"
    assert mass.get("no_title") == ("", "444")


@pytest.fixture
def workflow():
    """Fixture that returns a WorkflowResult instance."""
    return WorkflowResult(samples=[], workflow_checks=[])


def test_units(mass):
    """Test to show units are displayed when requested."""
    assert mass.mass_all == 10
    assert mass.get_reportable_value("mass_all", decimal_places=0) == "10 ng"


def test_units_missing_field(mass):
    """Test trying to get a reportable value on a missing field."""
    with pytest.raises(AttributeError):
        mass.get_reportable_value("missing_value")


def test_rounding(mass):
    """Test rounding."""
    # this shouldn't be allowed by the model, but let's check anyway
    mass = Mass(mass_all="10")
    assert mass.get_reportable_value("mass_all") == "10 ng"

    mass = Mass(mass_all=10.678)
    assert mass.get_reportable_value("mass_all", decimal_places=2) == "10.68 ng"


def test_rounding_wrong_type(mass):
    """Test trying to get a reportable value on a missing field."""
    mass = Mass(mass_all="10")
    with pytest.raises(TypeError):
        mass.get_reportable_value("mass_all", decimal_places=2)


def test_default_value(mass):
    """Test default value when getting reportable values."""
    mass = Mass(mass_all=None)
    assert mass.get_reportable_value("mass_all") == "N/A"
    assert mass.get_reportable_value("mass_all", default_value="NA") == "NA"


def test_sci_notation(mass):
    """Test that we get the value with sci notation."""
    mass = Mass(mass_all=0.0000001)
    assert mass.get_reportable_value("mass_all") == "1.00E-07 ng"
    mass = Mass(mass_all=100000000)
    assert mass.get_reportable_value("mass_all") == "1.00E+08 ng"


def test_load_client_fields(workflow, test_data):
    """Test client field loading."""
    assert workflow.load_client_fields(
        f"{test_data}/workflow_glue/client_fields.json") == {
            "operator": "Dwight Schrute",
            "requester": "Michael Scott",
            "organisation": "Dunder Mifflin",
            "sequencer": "GridION",
            "location": "Scranton",
            "interests": "bears, beets, battlestar"}


def test_load_client_fields_error(test_data):
    """Test client field loading."""
    workflow = WorkflowResult(samples=[], workflow_checks=[])
    assert workflow.load_client_fields(
        f"{test_data}/workflow_glue/client_fields_malformed.json") == {
            "error": "Error parsing client fields file."}


def sample(sample_checks):
    """Create a Sample instance."""
    return Sample(
        alias="alias",
        sample_type="test_sample",
        sample_checks=sample_checks,
        sample_pass=False,
    )


@pytest.mark.parametrize(
    (
        "checkresults,max_criteria,expected_qc_global_status,expected_qc_criteria"
    ),
    [
        (
            [
                CheckResult("example_check", "total_reads", True),
                CheckResult("example_check", "aligned_reads", True),
            ],
            4,
            {"status": True, "scope": "QC status"},
            [{"status": True, "scope": "All acceptance criteria met"}],
        ),
        (
            [
                CheckResult("example_check", "total_reads", True),
                CheckResult("example_check", "aligned_reads", False),
            ],
            2,
            {"status": False, "scope": "QC status"},
            [
                {
                    "status": False,
                    "category": "Example check category",
                    "scope": "Aligned reads",
                }
            ],
        ),
        (
            [
                CheckResult("example_check", "total_reads", False),
                CheckResult("example_check", "aligned_reads", False),
            ],
            1,
            {"status": False, "scope": "QC status"},
            [{"status": False, "scope": "2 acceptance criteria"}],
        ),
    ],
)
def test_get_reportable_qc_status(
    checkresults, max_criteria, expected_qc_global_status, expected_qc_criteria
):
    """Test QC components for report."""
    sample_instance = sample(checkresults)
    qc_global_status, qc_criteria = sample_instance.get_reportable_qc_status(
        max_criteria=max_criteria
    )
    assert qc_global_status == expected_qc_global_status
    assert qc_criteria == expected_qc_criteria


@pytest.mark.parametrize(
    ("checkresults,expected_sample_pass"),
    [
        (
            [
                CheckResult("example_check", "total_reads", True),
                CheckResult("example_check", "aligned_reads", True),
            ],
            True,
        ),
        (
            [
                CheckResult("example_check", "total_reads", True),
                CheckResult("example_check", "aligned_reads", False),
            ],
            False,
        ),
        (
            [
                CheckResult("example_check", "total_reads", False),
                CheckResult("example_check", "aligned_reads", False),
            ],
            False,
        ),
    ],
)
def test_get_sample_pass(checkresults, expected_sample_pass):
    """Test sample_pass check post init method."""
    sample_instance = sample(checkresults)
    assert sample_instance.sample_pass == expected_sample_pass


@pytest.mark.parametrize(
    "versions_input, error_msg, expected_result",
    [
        (
            "file", None,
            {"minimap2": "2.28-r1122", "samtools": "1.21", "fastcat": "0.22.0"},
        ),
        (
            "dir", None,  # dir
            {"minimap2": "2.28-r1122", "samtools": "1.21", "fastcat": "0.22.0"},
        ),
        ("file", r"No such file:", None),  # no existing file
    ],
)
def test_load_versions(tmp_path, workflow, versions_input, error_msg, expected_result):
    """Test parse_versions."""
    if error_msg:
        with pytest.raises(FileNotFoundError, match=error_msg):
            workflow.load_versions("non_existing_file.txt")
    else:
        versions = "minimap2,2.28-r1122\nsamtools,1.21\nfastcat,0.22.0"
        # Use tmp_path to create a temporary directory
        temp_dir = tmp_path / "temp_dir"
        temp_dir.mkdir()
        # Create a file inside the temporary directory
        versions_path = temp_dir / "versions.txt"
        versions_path.write_text(versions)
        if versions_input == "file":
            versions_path = versions_path
        elif versions_input == "dir":
            # return temp dir where the versions file was created
            versions_path = versions_path.parent
        assert (workflow.load_versions(versions_path) == expected_result)


@pytest.mark.parametrize(
    "keep_params,error_msg,expected_result",
    [
        (
            ["wfversion", "fastq"], None,
            {
                "wfversion": "v0.0.0",
                "fastq": "/wf-example/test_data/fastq",
            },
        ),
        (None, r"No such file:", None),
        (None, r"Invalid JSON file", None),
    ],
)
def test_parse_params(tmp_path, workflow, keep_params, error_msg, expected_result):
    """Test parse_params."""
    params = """
{"help":false,"wfversion":"v0.0.0","fastq":"/wf-example/test_data/fastq"}"""
    if error_msg:
        if "Invalid JSON" in error_msg:  # An empty file
            with pytest.raises(ValueError, match=error_msg):
                invalid_json = tmp_path / "invalid.json"
                invalid_json.touch()
                workflow.load_params(str(invalid_json))
        else:  # no file exist
            with pytest.raises(FileNotFoundError, match=fr'{error_msg}'):
                workflow.load_params("non_existing_file.json")
    else:
        # Create a file inside the temporary directory
        params_path = tmp_path / "params.json"
        params_path.write_text(params)
        assert (workflow.load_params(params_path, keep_params) == expected_result)
