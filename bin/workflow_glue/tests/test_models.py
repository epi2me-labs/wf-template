"""Test the results_schema and results_schema_helper scripts."""
import pytest
from workflow_glue.models.common import SampleType
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
