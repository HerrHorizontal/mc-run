# -*- coding: utf-8 -*-
"""Executables compiled from source code, built once locally and shipped with law jobs."""

import hashlib
import os

from generation.framework.utils import run_command
from law.logger import get_logger

logger = get_logger(__name__)


class CompiledExecutable:
    """Executable compiled from source code, built once in $ANALYSIS_PATH/tmp/<name> and shipped
    with law jobs, see `ShipExecutablesMixin`.

    The file name contains a hash of the compile command and the contents of the source and
    setup files, so that a changed executable never gets mixed up with an older build.

    Args:
        name (str): Base name of the executable
        sources (List[str]): Paths of the source files
        compile_cmd (str): Bash command compiling the sources, with the placeholders `{sources}`
            and `{executable}`
        environment (Callable[[], Dict]): Returns the environment of the compile command
        setup_files (List[str]): Further files that determine the build, e.g. the setup script
            of the environment
    """

    def __init__(self, name, sources, compile_cmd, environment, setup_files=()):
        self.name = name
        self.sources = list(sources)
        self.compile_cmd = compile_cmd
        self.environment = environment
        self.setup_files = list(setup_files)
        self._path = None

    @property
    def file_name(self):
        """File name of the executable with the hash of its build inputs."""
        digest = hashlib.sha1(self.compile_cmd.encode())
        for path in self.sources + self.setup_files:
            with open(path, "rb") as f:
                digest.update(f.read())
        return "{}_{}".format(self.name, digest.hexdigest()[:12])

    def path(self):
        """Path of the executable: the one shipped with the job in remote jobs, otherwise the
        local build, which is compiled if it does not exist yet.

        Returns:
            str: Path to the executable
        """
        if self._path is None:
            self._path = self._shipped_path() or self._build()
        return self._path

    def job_input(self):
        """The executable as a law job input file. It is transferred from the local build
        directory and keeps its file name in the job.

        Returns:
            law.JobInputFile: Executable to ship with the job
        """
        import law

        return law.JobInputFile(self.path(), copy=False)

    def _shipped_path(self):
        if not os.getenv("LAW_JOB_INIT_DIR"):
            return None
        path = os.path.join(os.environ["LAW_JOB_INIT_DIR"], self.file_name)
        return path if os.path.isfile(path) else None

    def _build(self):
        build_dir = os.path.join(os.path.expandvars("$ANALYSIS_PATH"), "tmp", self.name)
        executable = os.path.join(build_dir, self.file_name)
        if os.path.isfile(executable):
            return executable
        logger.info("Compiling {} into {}".format(self.file_name, build_dir))
        os.makedirs(build_dir, exist_ok=True)
        # compile into a temporary file, so that parallel processes never use a partial build
        tmp_executable = "{}.{}.tmp".format(executable, os.getpid())
        compile_cmd = self.compile_cmd.format(
            sources=" ".join('"{}"'.format(source) for source in self.sources),
            executable=tmp_executable,
        )
        run_command(["bash", "-c", compile_cmd], env=self.environment())
        os.replace(tmp_executable, executable)
        return executable
