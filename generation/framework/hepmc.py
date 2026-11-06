# -*- coding: utf-8 -*-
"""HepMC converter: build, ship with jobs and convert generator output."""

import os

from generation.framework.utils import run_command, set_environment_variables
from law.logger import get_logger

logger = get_logger(__name__)


HEPMC_CONVERTER_SOURCE = os.path.join(os.path.dirname(__file__), "hepmc_convert.cc")
HEPMC_SETUP_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "setup", "setup_hepmc.sh")
)
HEPMC_CONVERTER_COMPILE = (
    'g++ -O2 -DHEPMC3_USE_COMPRESSION=1 -DHEPMC3_Z_SUPPORT=1 "{source}" -o "{executable}" '
    "$(HepMC3-config --cxxflags --libs --rootIO) $(root-config --cflags --libs) -lz"
)


def hepmc_environment():
    """Environment of the HepMC converter from setup/setup_hepmc.sh.

    Raises:
        RuntimeError: The environment is not available on this OS

    Returns:
        Dict: Environment variables
    """
    hepmc_env = set_environment_variables(HEPMC_SETUP_SCRIPT)
    if not hepmc_env.get("HEPMC_LCG_PLATFORM"):
        raise RuntimeError(
            "Sourcing the HepMC environment from {} failed!".format(HEPMC_SETUP_SCRIPT)
        )
    return hepmc_env


def hepmc_converter_name():
    """Name of the HepMC converter executable, keyed by the hash of its source code, the
    environment setup script, the compile command and the LCG platform (e.g. x86_64-el9-gcc15-opt).

    Returns:
        str: File name of the converter executable
    """
    import hashlib

    digest = hashlib.sha1()
    for path in (HEPMC_CONVERTER_SOURCE, HEPMC_SETUP_SCRIPT):
        with open(path, "rb") as f:
            digest.update(f.read())
    digest.update(HEPMC_CONVERTER_COMPILE.encode())
    digest.update(hepmc_environment()["HEPMC_LCG_PLATFORM"].encode())
    return "hepmc_convert_{}".format(digest.hexdigest()[:12])


def get_hepmc_converter():
    """Return the path of the HepMC converter, building it if not already available.

    The executable is cached in $ANALYSIS_PATH/tmp/hepmc_convert. In remote jobs, an executable
    shipped with the job (see `hepmc_converter_job_input`) is used if it matches the source code
    and the OS of the job, otherwise it is compiled in the job.

    Returns:
        str: Path to the converter executable
    """
    import glob
    import shutil
    import tempfile

    name = hepmc_converter_name()
    build_dir = os.path.join(os.path.expandvars("$ANALYSIS_PATH"), "tmp", "hepmc_convert")
    executable = os.path.join(build_dir, name)
    if os.path.isfile(executable) and os.access(executable, os.X_OK):
        return executable

    # write into a temporary file first and move it into place afterwards,
    # so that parallel workers never pick up a partially written executable
    os.makedirs(build_dir, exist_ok=True)
    fd, tmp_executable = tempfile.mkstemp(dir=build_dir, prefix=".hepmc_convert.")
    os.close(fd)
    # law appends a hash of the source path to the names of job input files
    shipped_executables = []
    if os.getenv("LAW_JOB_INIT_DIR"):
        shipped_executables = sorted(
            glob.glob(os.path.join(os.environ["LAW_JOB_INIT_DIR"], name))
            + glob.glob(os.path.join(os.environ["LAW_JOB_INIT_DIR"], name + "_*"))
        )
    try:
        if shipped_executables:
            logger.info(
                "Using HepMC converter shipped with the job: {}".format(
                    os.path.basename(shipped_executables[0])
                )
            )
            shutil.copyfile(shipped_executables[0], tmp_executable)
        else:
            logger.info(f"Compiling HepMC converter {name} into {build_dir}")
            run_command(
                [
                    "bash",
                    "-c",
                    HEPMC_CONVERTER_COMPILE.format(
                        source=HEPMC_CONVERTER_SOURCE, executable=tmp_executable
                    ),
                ],
                env=hepmc_environment(),
            )
        os.chmod(tmp_executable, 0o755)
        os.replace(tmp_executable, executable)
    finally:
        if os.path.exists(tmp_executable):
            os.remove(tmp_executable)
    return executable


_hepmc_converter_job_input = None


def hepmc_converter_job_input():
    """Build the HepMC converter locally, if needed, and return it as a law job input
    file, so that remote jobs do not need to compile it. The converter is built only once per
    submission.

    Returns:
        law.JobInputFile: Converter executable to ship with the job
    """
    import law

    global _hepmc_converter_job_input
    if _hepmc_converter_job_input is None:
        _hepmc_converter_job_input = law.JobInputFile(
            get_hepmc_converter(), share=True, render=False
        )
    return _hepmc_converter_job_input


# output formats of the HepMC converter, all of them can be read by Rivet
HEPMC_FORMATS = ("root", "hepmc3", "hepmc3.gz")


def convert_hepmc(input_files, output_file, hepmc_format="root", compression=209):
    """Convert HepMC ascii files into a single HepMC3 file of the given format.

    The converter checks that all event records of the input files are converted.

    Args:
        input_files (List[str]): Paths of the HepMC2/HepMC3 ascii input files
        output_file (str): Path of the file to write
        hepmc_format (str): Output format, one of `HEPMC_FORMATS`: `root` (HepMC3 ROOT
            TTree), `hepmc3` (HepMC3 ascii) or `hepmc3.gz` (gzip-compressed HepMC3 ascii)
        compression (int): ROOT compression setting (100 * algorithm + level) of `root` output,
            e.g. 209 = LZMA 9

    Raises:
        ValueError: Unknown output format
        RuntimeError: Conversion or verification of the written file failed
    """
    if hepmc_format not in HEPMC_FORMATS:
        raise ValueError("Unknown HepMC output format: {}".format(hepmc_format))
    run_command(
        [get_hepmc_converter(), "-f", hepmc_format, "-c", str(compression), output_file]
        + list(input_files),
        env=hepmc_environment(),
    )
