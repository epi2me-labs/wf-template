from collections import defaultdict
from pathlib import Path
import re

import pandas as pd
import pysam


INPUT_TYPES_EXTENSIONS = {
    "fastq": ["fastq", "fastq.gz", "fq", "fq.gz"],
    "bam": ["bam", "ubam"],
}


def validate_xam_index(xam_file):
    """Use fetch to validate the index.

    Invalid indexes will fail the call with a ValueError:
    ValueError: fetch called on bamfile without index
    """
    with pysam.AlignmentFile(xam_file, check_sq=False) as alignments:
        try:
            alignments.fetch()
            has_valid_index = True
        except ValueError:
            has_valid_index = False
    return has_valid_index


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


def create_preliminary_meta(path, input_type, output_type):
    """Create a dict of sequence IDs / names and run_ids.

    :param path: can be a single target file, a list of target files, or a directory
        containing target files.
    :param input_type: can either be "fastq" or "bam"
    :param output_type: either "fastq" or "bam"; is "fastq" when `xam_ingress` was run
        with `--return_fastq`

    For FASTQ files, the run IDs can be present in the header lines in the format
    `runid=...` or `RD:Z:...`. If both are present, an error is thrown.
    """
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
        raise ValueError(
            f"`path` needs to be a list or path to a file or directory (got '{path}')."
        )
    # Metadata specific for xam_ingress
    n_primary = 0
    n_unmapped = 0
    src_xam = None
    # Ensure that there is a single file, and that it is not s3
    if len(target_files) == 1 and 'test_data_from_S3' not in target_files[0].as_posix():
        src_xam = target_files[0].as_posix()
    src_xai = None
    if src_xam:
        if Path(src_xam + '.bai').exists() and validate_xam_index(src_xam):
            src_xai = src_xam + '.bai'
    basecall_models = set()
    for file in target_files:
        if input_type == "fastq":
            with pysam.FastxFile(file) as f:
                for entry in f:
                    names.append(entry.name)
                    run_id = None
                    basecall_model = None
                    # only look for things in the FASTQ header comment if there is one
                    if entry.comment is None:
                        continue
                    # check for "regular" tags first
                    if "runid=" in entry.comment:
                        (run_id,) = re.findall(r"runid=([^\s]+)", entry.comment)
                    if "basecall_model_version_id=" in entry.comment:
                        (basecall_model,) = re.findall(
                            r"basecall_model_version_id=([^\s]+)", entry.comment
                        )
                    # now check for SAM tags (which could come from running `samtools
                    # fastq` on dorado output)
                    if "RD:Z:" in entry.comment:
                        # explode if we already found a run ID
                        if run_id is not None:
                            raise ValueError(
                                "Found 'runid=' and 'RD:Z:' in "
                                f"FASTQ header '{entry.comment}'."
                            )
                        (run_id,) = re.findall(r"RD:Z:([^\s]+)", entry.comment)
                    if "RG:Z:" in entry.comment:
                        if basecall_model is not None:
                            raise ValueError(
                                "Found 'basecall_model_version_id=' and 'RG:Z:' in "
                                f"FASTQ header '{entry.comment}'."
                            )
                        rg = entry.comment.split("RG:Z:")[1].split()[0]
                        basecall_model = rg.split("_barcode")[0].split("_", 1)[1]
                    if run_id is not None:
                        run_ids.add(run_id)
                    if basecall_model is not None:
                        basecall_models.add(basecall_model)
        else:
            unaligned = is_unaligned(file)
            with pysam.AlignmentFile(file, check_sq=False) as f:
                xam_sorted = f.header.get('HD', {}).get('SO') == 'coordinate'
                # Check if the data are aligned
                if not unaligned and not xam_sorted:
                    src_xam = None
                    src_xai = None
                # map (run_id, basecall_model) pairs to RG.IDs in order
                # to determine if RGs have had collision avoidance applied
                runid_model_to_rgid = defaultdict(set)
                # populate metamap items from RG.DS
                for read_group in f.header.get("RG", []):
                    rg_id = read_group.get("ID")
                    rg_runid = None
                    rg_basecall_model = None
                    for ds_kv in read_group.get("DS", "").split():
                        k, v = ds_kv.split("=", 1)
                        if k == "runid":
                            rg_runid = v
                            run_ids.add(rg_runid)
                        elif k == "basecall_model":
                            rg_basecall_model = v
                            basecall_models.add(rg_basecall_model)
                    if rg_id and rg_runid and rg_basecall_model:
                        compound_key = f"{rg_runid}/{rg_basecall_model}"
                        runid_model_to_rgid[compound_key].add(rg_id)
                for entry in f:
                    # Just take unmapped reads and primary alignments
                    if entry.is_unmapped:
                        n_unmapped += 1
                    else:
                        if not (entry.is_secondary or entry.is_supplementary):
                            n_primary += 1
                    run_id = dict(entry.tags).get("RD")
                    names.append(entry.query_name)
                    if run_id is not None:
                        run_ids.add(run_id)
                # looks like RG.IDs have collided without merging (CW-4608)
                if any(len(rgids) > 1 for rgids in runid_model_to_rgid.values()):
                    raise ValueError(
                        "BAM appears to have multiple RG.IDs corresponding to "
                        "the same sequencing run in the same file. Suspect that "
                        "this BAM was created with samtools merge without -c."
                    )
    # add n_reads, run_ids, etc to the dict to be checked later
    prel_meta = dict(
        names=names,
        run_ids=run_ids,
        basecall_models=list(basecall_models)
    )
    if output_type == "fastq":
        prel_meta["n_seqs"] = len(names)
    else:
        prel_meta["n_primary"] = n_primary
        prel_meta["n_unmapped"] = n_unmapped
        prel_meta["src_xam"] = src_xam
        prel_meta["src_xai"] = src_xai

    return prel_meta


def amend_meta_for_output(meta, output_type, chunk_size, clear_stats_info):
    """Amend the metadata dict for the output type.

    create_preliminary_meta() does double duty for both input and output files.
    This function amends the metadata dict for the output type.
    """
    # additional meta data for fastq output
    if output_type == "fastq":
        meta["n_fastq"] = 1
        if chunk_size is not None:
            meta["n_fastq"] = meta["n_seqs"] // chunk_size + int(meta["n_seqs"] % chunk_size > 0)
        meta["group_key"] = {"groupSize": meta["n_fastq"], "groupTarget": meta["alias"]}
        meta["group_index"] = [meta["alias"] + f"_{i}" for i in range(meta["n_fastq"])]

    # clear things that aren't present in some no-stats cases
    if clear_stats_info:
        meta["run_ids"] = []
        meta["basecall_models"] = []
        if output_type == "fastq":
            meta["n_seqs"] = None
        elif output_type == "bam":
            meta['src_xam'] = None
            meta['src_xai'] = None
            meta["n_primary"] = None
            meta["n_unmapped"] = None

    return meta


def create_metadict(**kwargs):
    """Create dict of metadata and check if required values are present."""
    if "alias" not in kwargs or kwargs["alias"] is None:
        raise ValueError("Meta data needs 'alias'.")
    defaults = dict(barcode=None, type="test_sample", run_ids=[], basecall_models=[])
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
            sq_lines = [{
                "SN": sq["SN"],
                "LN": sq["LN"],
                "M5": sq.get("M5"),
            } for sq in f.header.get("SQ", [])]
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


def get_valid_inputs(input_path, input_type, output_type, sample_sheet, params):
    """Get valid input paths and corresponding metadata."""
    # get functions for FASTQ or BAM case
    check_input_type(input_type)
    input_path = Path(input_path)
    # find the valid inputs
    valid_inputs = []

    # handle file case first
    if input_path.is_file():
        # get sequence names and run IDs
        prel_meta = create_preliminary_meta(
            input_path,
            input_type,
            output_type,
        )
        del prel_meta['names']
        meta = create_metadict(
            alias=params["sample"]
            if params["sample"] is not None
            else input_path.name.split(".")[0],
            **prel_meta
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
            prel_meta = create_preliminary_meta(
                top_dir_target_files,
                input_type,
                output_type,
            )

            del prel_meta['names']
            meta = create_metadict(
                alias=params["sample"]
                if params["sample"] is not None
                else input_path.name,
                **prel_meta
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
                prel_meta = create_preliminary_meta(
                    subdir,
                    input_type,
                    output_type,
                )
                del prel_meta['names']
                barcode = subdir.name
                meta = create_metadict(
                    alias=barcode,
                    barcode=barcode,
                    **prel_meta
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
                # ingress uses `groupKey` for the 'analysis_group' column in the sample
                # sheet
                if "analysis_group" in sample_sheet.columns:
                    analysis_group_counts = sample_sheet.value_counts("analysis_group")
                    sample_sheet["analysis_group"] = [
                        {"groupSize": analysis_group_counts[grp], "groupTarget": grp}
                        for grp in sample_sheet["analysis_group"]
                    ]
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
    # unless allowed, set the path to `None` for all samples that had multiple basecall
    # models
    if not params["wf"]["allow_multiple_basecall_models"]:
        for i, (meta, path) in enumerate(valid_inputs):
            if len(meta["basecall_models"]) > 1:
                valid_inputs[i][1] = None
    return valid_inputs
