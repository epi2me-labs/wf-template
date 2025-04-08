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
            "unit": "ng"})


@pytest.fixture
def mass():
    """Fixture that returns a Mass instance."""
    return Mass(mass_all=10)


def test_units(mass):
    """Test to show units are displayed when requested."""
    assert mass.mass_all == 10
    assert mass.get_reportable_value("mass_all", 0) == "10 ng"


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


def test_load_client_fields(test_data):
    """Test client field loading."""
    workflow = WorkflowResult(samples=[], workflow_checks=[])
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
            [{"status": True, "scope": "QC status"}],
            [{"status": True, "scope": "All acceptance criteria met"}],
        ),
        (
            [
                CheckResult("example_check", "total_reads", True),
                CheckResult("example_check", "aligned_reads", False),
            ],
            2,
            [{"status": False, "scope": "QC status"}],
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
            [{"status": False, "scope": "QC status"}],
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
