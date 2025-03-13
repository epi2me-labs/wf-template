"""Test the results_schema and results_schema_helper scripts."""
from workflow_glue.models.common import SampleType
from workflow_glue.models.custom import CheckResult


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
