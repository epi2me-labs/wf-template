"""Create workflow report."""
import json

from dominate.tags import p
from ezcharts.components import fastcat
from ezcharts.components.reports import labs
from ezcharts.layout.snippets import Tabs
from ezcharts.layout.snippets.table import DataTable
import pandas as pd

from .util import get_named_logger, wf_parser  # noqa: ABS101


def main(args):
    """Run the entry point."""
    logger = get_named_logger("Report")
    report = labs.LabsReport(
        "Workflow Template Sequencing report", "wf-template",
        args.params, args.versions, args.wf_version)

    client_fields = None
    if args.client_fields:
        with open(args.client_fields) as f:
            try:
                client_fields = json.load(f)
            except json.decoder.JSONDecodeError:
                error = "ERROR: Client info is not correctly formatted"

        with report.add_section("Workflow Metadata", "Workflow Metadata"):
            if client_fields:
                df = pd.DataFrame.from_dict(
                    client_fields, orient="index", columns=["Value"])
                df.index.name = "Key"

                # Examples from the client had lists as values so join lists
                # for better display
                df['Value'] = df.Value.apply(
                    lambda x: ', '.join(
                        [str(i) for i in x]) if isinstance(x, list) else x)

                DataTable.from_pandas(df)
            else:
                p(error)

    with open(args.metadata) as metadata:
        sample_details = [{
            'sample': d['alias'],
            'type': d['type'],
            'barcode': d['barcode']
        } for d in json.load(metadata)]

    if args.stats:
        with report.add_section("Read summary", "Read summary"):
            names = tuple(d['sample'] for d in sample_details)
            stats = tuple(args.stats)
            if len(stats) == 1:
                stats = stats[0]
                names = names[0]
            fastcat.SeqSummary(stats, sample_names=names)

    with report.add_section("Sample Metadata", "Sample Metadata"):
        tabs = Tabs()
        for d in sample_details:
            with tabs.add_tab(d["sample"]):
                df = pd.DataFrame.from_dict(d, orient="index", columns=["Value"])
                df.index.name = "Key"
                DataTable.from_pandas(df)

    report.write(args.report)
    logger.info(f"Report written to {args.report}.")


def argparser():
    """Argument parser for entrypoint."""
    parser = wf_parser("report")
    parser.add_argument("report", help="Report output file")
    parser.add_argument(
        "--stats", nargs='+',
        help="Fastcat per-read stats, ordered as per entries in --metadata.")
    parser.add_argument(
        "--metadata", default='metadata.json', required=True,
        help="sample metadata")
    parser.add_argument(
        "--versions", required=True,
        help="directory containing CSVs containing name,version.")
    parser.add_argument(
        "--params", default=None, required=True,
        help="A JSON file containing the workflow parameter key/values")
    parser.add_argument(
        "--client_fields", default=None, required=False,
        help="A JSON file containing useful key/values for display")
    parser.add_argument(
        "--wf_version", default='unknown',
        help="version of the executed workflow")
    return parser
