"""Test the results_schema and results_schema_helper scripts."""
import workflow_glue.results_schema as wf


def test_enum_comparisons():
    """Test enum comparison."""
    dummy = wf.Sample(
        alias="dummy",
        barcode="barcode01",
        sample_type=wf.SampleType.test_sample,
        sample_pass=True,
        sample_checks=[],
        results={}
    )
    # Correct model comparison
    assert dummy.sample_type == wf.SampleType.test_sample
    # Old method still valid
    assert dummy.sample_type == wf.SampleType.test_sample.value
    # String comparisons still work but not advised
    assert dummy.sample_type == "test_sample"
