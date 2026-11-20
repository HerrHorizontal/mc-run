# -*- coding: utf-8 -*-
"""HepMC converter of generator output."""

import os

from generation.framework.executable import CompiledExecutable
from generation.framework.utils import run_command, set_environment_variables
from law.logger import get_logger

logger = get_logger(__name__)


HEPMC_CONVERTER_SOURCE = os.path.join(os.path.dirname(__file__), "hepmc_convert.cc")
HEPMC_SETUP_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "setup", "setup_hepmc.sh")
)
HEPMC_CONVERTER_COMPILE = (
    'g++ -O2 -DHEPMC3_USE_COMPRESSION=1 -DHEPMC3_Z_SUPPORT=1 {sources} -o "{executable}" '
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


HEPMC_CONVERTER = CompiledExecutable(
    "hepmc_convert",
    sources=[HEPMC_CONVERTER_SOURCE],
    compile_cmd=HEPMC_CONVERTER_COMPILE,
    environment=hepmc_environment,
    setup_files=[HEPMC_SETUP_SCRIPT],
)


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
        compression (int): ROOT compression setting (100 * algorithm + level), e.g. 209 = LZMA 9,
            for `hepmc3.gz` output the level is used as gzip level

    Raises:
        ValueError: Unknown output format
        RuntimeError: Conversion or verification of the written file failed
    """
    if hepmc_format not in HEPMC_FORMATS:
        raise ValueError("Unknown HepMC output format: {}".format(hepmc_format))
    run_command(
        [HEPMC_CONVERTER.path(), "-f", hepmc_format, "-c", str(compression), output_file]
        + list(input_files),
        env=hepmc_environment(),
    )


def generate_into_converter(
    generator_cmd,
    generator_env,
    hepmc_file,
    output_file,
    n_events,
    hepmc_format="root",
    compression=209,
    cwd=None,
    poll_interval=1.0,
):
    """Run an event generator and convert its HepMC output on the fly.

    A named pipe (FIFO) is created at the path the generator writes its HepMC output to, and the
    converter reads from it while the generator runs. The converter checks that exactly `n_events`
    events were converted. The generator and converter run in separate processes with their own
    environments. If one of them fails, the other one is stopped, so that neither of them blocks
    forever on the pipe.

    Args:
        generator_cmd (List[str]): Command running the event generation
        generator_env (Dict): Environment of the generator
        hepmc_file (str): Path of the HepMC file the generator writes, replaced by the pipe
        output_file (str): Path of the file to write
        n_events (int): Number of events the generator produces
        hepmc_format (str): Output format, one of `HEPMC_FORMATS`
        compression (int): Compression setting, see `convert_hepmc`
        cwd (str): Working directory of the generator
        poll_interval (float): Seconds between status checks of both processes

    Raises:
        ValueError: Unknown output format
        RuntimeError: Generator or converter failed
    """
    import errno
    import subprocess
    import tempfile
    import time

    if hepmc_format not in HEPMC_FORMATS:
        raise ValueError("Unknown HepMC output format: {}".format(hepmc_format))
    converter_cmd = [
        HEPMC_CONVERTER.path(),
        "-f",
        hepmc_format,
        "-c",
        str(compression),
        "-n",
        str(n_events),
        output_file,
        hepmc_file,
    ]

    def unblock_reader():
        # a reader blocks in open() until a writer opens the pipe, e.g. if the generator failed
        # before opening its output: open and close the pipe for writing, so that it reads EOF
        try:
            os.close(os.open(hepmc_file, os.O_WRONLY | os.O_NONBLOCK))
        except OSError as e:
            if e.errno != errno.ENXIO:  # no reader has the pipe open (anymore)
                raise

    def stop(process):
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def log_output(name, log, failed):
        log.seek(0)
        output = log.read().decode(errors="replace")
        (logger.error if failed else logger.info)("{} output:\n{}".format(name, output))

    if os.path.lexists(hepmc_file):
        os.remove(hepmc_file)
    os.mkfifo(hepmc_file)
    logger.info("Running: {}...".format(" ".join(generator_cmd[:3])))
    logger.info("Converting on the fly into {} ({})".format(output_file, hepmc_format))
    generator = converter = None
    # outputs go to temporary files instead of pipes, which could fill up and block the processes
    with tempfile.TemporaryFile() as generator_log, tempfile.TemporaryFile() as converter_log:
        try:
            converter = subprocess.Popen(
                converter_cmd,
                env=hepmc_environment(),
                stdout=converter_log,
                stderr=subprocess.STDOUT,
            )
            generator = subprocess.Popen(
                generator_cmd,
                env=generator_env,
                cwd=cwd,
                stdout=generator_log,
                stderr=subprocess.STDOUT,
            )
            # wait for the generator, stop it if the converter fails, as it could block on the
            # pipe otherwise (opening it or writing to it without a reader)
            while generator.poll() is None:
                if converter.poll() not in (None, 0):
                    logger.error("Converter failed, stopping the generator")
                    stop(generator)
                    break
                time.sleep(poll_interval)
            if converter.poll() is None and generator.returncode != 0:
                stop(converter)
            # the generator closed the pipe, the converter finishes once it read all events
            while converter.poll() is None:
                unblock_reader()
                try:
                    converter.wait(timeout=poll_interval)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            stop(generator)
            stop(converter)
            if os.path.lexists(hepmc_file):
                os.remove(hepmc_file)
        log_output("Generator", generator_log, generator.returncode != 0)
        log_output("Converter", converter_log, converter.returncode != 0)
    if generator.returncode != 0 or converter.returncode != 0:
        raise RuntimeError(
            "Event generation with on-the-fly conversion failed (generator exit code {}, "
            "converter exit code {})!".format(generator.returncode, converter.returncode)
        )
