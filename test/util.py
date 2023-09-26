from pathlib import Path
import re

import pandas as pd
import pysam


INPUT_TYPES_EXTENSIONS = {
    "fastq": ["fastq", "fastq.gz", "fq", "fq.gz"],
    "bam": ["bam", "ubam"],
}


def check_input_type(input_type):
    if input_type not in INPUT_TYPES_EXTENSIONS:
        raise ValueError(
            f"`input_type` needs to be one of {INPUT_TYPES_EXTENSIONS.keys()}."
        )


def is_target_file(file, input_type):
    """Check if `file` is of `input_type`."""
    if not file.is_file():
        return False
    exts = INPUT_TYPES_EXTENSIONS[input_type]
    return any(map(lambda ext: file.name.endswith(ext), exts))


def get_target_files(path, input_type):
    """Return a list of target files in the directory."""
    return list(filter(lambda file: is_target_file(file, input_type), path.iterdir()))


def get_names_and_run_ids(path, input_type):
    """Create a dict of sequence IDs / names and run_ids.

    `path` can be a single target file, a list of target files, or a directory
    containing target files."""
    check_input_type(input_type)
    names = []
    run_ids = set()
    if isinstance(path, list):
        target_files = path
    elif path.is_dir():
        target_files = get_target_files(path, input_type)
    elif path.is_file():
        target_files = [path]
    else:
        raise ValueError("`path` needs to be a list or path to a file or directory.")
    for file in target_files:
        if input_type == "fastq":
            with pysam.FastxFile(file) as f:
                for entry in f:
                    name = entry.name
                    (run_id,) = re.findall(r"runid=([^\s]+)", entry.comment) or [None]
                    names.append(name)
                    if run_id is not None:
                        run_ids.add(run_id)
        else:
            with pysam.AlignmentFile(file, check_sq=False) as f:
                for entry in f:
                    name = entry.query_name
                    run_id = dict(entry.tags).get("RD")
                    names.append(name)
                    if run_id is not None:
                        run_ids.add(run_id)
    return dict(names=names, run_ids=run_ids)


def create_metadict(**kwargs):
    """Create dict of metadata and check if required values are present."""
    if "alias" not in kwargs or kwargs["alias"] is None:
        raise ValueError("Meta data needs 'alias'.")
    defaults = dict(barcode=None, type="test_sample", run_ids=[])
    if "run_ids" in kwargs:
        # cast to sorted list to compare to workflow output
        kwargs["run_ids"] = sorted(list(kwargs["run_ids"]))
    defaults.update(kwargs)
    defaults["alias"] = defaults["alias"].replace(" ", "_")
    return defaults


def is_unaligned(path):
    """Check if uBAM.

    When a single file, checks if there are `@SQ` lines in the header. When a directory,
    return `True` if all XAM files are missing `@SQ` lines. If there are mixed headers
    (i.e. some have `@SQ` lines and some don't or the `@SQ` lines between different
    files don't match), blow up.
    """
    if path.is_file():
        target_files = [path]
    elif path.is_dir():
        target_files = get_target_files(path, "bam")
    else:
        raise ValueError("`path` is neither file nor directory.")

    first_sq_lines = None
    for target_file in target_files:
        with pysam.AlignmentFile(target_file, check_sq=False) as f:
            sq_lines = f.header["SQ"]
        if first_sq_lines is None:
            # first file
            first_sq_lines = sq_lines
        else:
            # subsequent file
            if first_sq_lines != sq_lines:
                raise ValueError(f"'{path}' contains (u)BAM files with mixed headers.")
    # if no error was raised, all files had the same `@SQ` files and we can determine
    # `is_unaligned` based on the `@SQ` lines of the first file
    return not first_sq_lines


def get_valid_inputs(input_path, input_type, sample_sheet, params):
    """Get valid input paths and corresponding metadata."""
    # get functions for FASTQ or BAM case
    check_input_type(input_type)
    input_path = Path(input_path)
    # find the valid inputs
    valid_inputs = []
    # handle file case first
    if input_path.is_file():
        run_ids = get_names_and_run_ids(input_path, input_type)["run_ids"]
        meta = create_metadict(
            alias=params["sample"]
            if params["sample"] is not None
            else input_path.name.split(".")[0],
            run_ids=run_ids,
        )
        valid_inputs.append([meta, input_path])
    else:
        # is a directory --> check if target files in top-level dir or in sub-dirs
        top_dir_target_files = get_target_files(input_path, input_type)
        subdirs_with_target_files = [
            x
            for x in input_path.iterdir()
            if x.is_dir() and get_target_files(x, input_type)
        ]
        if top_dir_target_files and subdirs_with_target_files:
            raise ValueError(
                f"Input directory '{input_path}' cannot contain {input_type.upper()} "
                f"files and sub-directories with {input_type.upper()} files."
            )
        # make sure we only have target files in either (top-level dir or sub-dirs) and
        # not both
        if not top_dir_target_files and not subdirs_with_target_files:
            raise ValueError(
                f"Input directory '{input_path}' contains neither sub-directories "
                f"nor {input_type.upper()} files."
            )
        if top_dir_target_files:
            # get the run IDs of all files
            run_ids = get_names_and_run_ids(top_dir_target_files, input_type)["run_ids"]
            meta = create_metadict(
                alias=params["sample"]
                if params["sample"] is not None
                else input_path.name,
                run_ids=run_ids,
            )
            valid_inputs.append([meta, input_path])
        else:
            # iterate over the sub-directories
            for subdir in subdirs_with_target_files:
                # make sure we don't have sub-sub-directories containing target files
                if any(
                    get_target_files(x, input_type)
                    for x in subdir.iterdir()
                    if x.is_dir()
                ):
                    raise ValueError(
                        f"Input directory '{input_path}' cannot contain more than one "
                        f"level of sub-directories with {input_type.upper()} files."
                    )
                # handle unclassified
                if subdir.name == "unclassified" and not params["analyse_unclassified"]:
                    continue
                # get the run IDs of all files
                run_ids = get_names_and_run_ids(subdir, input_type)["run_ids"]
                barcode = subdir.name
                meta = create_metadict(
                    alias=barcode,
                    barcode=barcode,
                    run_ids=run_ids,
                )
                valid_inputs.append([meta, subdir])
            # parse the sample sheet in case there was one
            if sample_sheet is not None:
                sample_sheet = pd.read_csv(sample_sheet).set_index(
                    # set 'barcode' as index while also keeping the 'barcode' column in
                    # the df
                    "barcode",
                    drop=False,
                )
                # now, get the corresponding inputs for each entry in the sample sheet
                # (sample sheet entries for which no input directory was found will have
                # `None` as their input path in `valid_inputs`); we need a dict mapping
                # barcodes to valid input paths for this
                valid_inputs_dict = {
                    path.name: [meta, path] for meta, path in valid_inputs
                }
                # reset `valid_inputs`
                valid_inputs = []
                for barcode, sample_sheet_entry in sample_sheet.iterrows():
                    try:
                        meta, path = valid_inputs_dict[barcode]
                    except KeyError:
                        meta, path = {}, None
                    meta.update(dict(sample_sheet_entry))
                    valid_inputs.append([create_metadict(**dict(meta)), path])
    # Finally, in case of XAM, loop over the valid inputs again and check if
    # they are uBAM. If so and not `keep_unaligned`, set the path to `None` and
    # the run IDs to `[]`.
    if input_type == "bam":
        valid_inputs_tmp = []
        for meta, path in valid_inputs:
            if path is not None:
                meta["is_unaligned"] = is_unaligned(path)
                if meta.get("is_unaligned") and not params["wf"]["keep_unaligned"]:
                    path = None
                    meta["run_ids"] = []
            valid_inputs_tmp.append([meta, path])
        valid_inputs = valid_inputs_tmp
    return valid_inputs
