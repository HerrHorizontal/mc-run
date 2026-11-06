import os

import law
from law.logger import get_logger

law.contrib.load("git")

logger = get_logger(__name__)


class BundleRepo(law.git.BundleGitRepository):
    """
    Bundle the repository (including submodules) into a local archive.

    The archive is small (a few MB at most) and is therefore shipped via HTCondor with each job.
    """

    # patterns excluded at any depth of the repository
    exclude_files = [
        "tmp",
        "*~",
        "*.pyc",
        ".vscode/",
        "*.db*",
        "*.tex",
        "*.dat",
        "logs",
        "plots",
    ]

    # paths relative to the repository root that are excluded only at exactly this location,
    # i.e. documentation, tests and software that is not needed in batch jobs
    exclude_paths = [
        "docs",
        "data*",
        "software",
        "kafe2",
        "law/assets",
        "law/docker",
        "law/docs",
        "law/examples",
        "law/tests",
        "luigi/doc",
        "luigi/examples",
        "luigi/test",
        # web visualiser of the central scheduler, jobs use the local scheduler
        "luigi/luigi/static",
    ]

    include_files = ["inputfiles/*/*/Run.dat"]

    version = None
    task_namespace = None
    default_store = "$ANALYSIS_PATH/tmp/bundles"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # law strips the repository path from absolute exclude paths and passes them as anchored
        # patterns (leading "/") to rsync, so they only match at the repository root
        repo_path = self.get_repo_path()
        self.exclude_files = list(self.exclude_files) + [
            os.path.join(repo_path, p) for p in self.exclude_paths
        ]

    def get_repo_path(self):
        # required by BundleGitRepository
        return os.environ["ANALYSIS_PATH"]

    def output(self):
        repo_base = os.path.basename(self.get_repo_path())
        store = os.path.expandvars(os.path.expanduser(self.default_store))
        return law.LocalFileTarget(
            os.path.join(store, f"{repo_base}.{self.checksum}.tgz")
        )

    @law.decorator.safe_output
    def run(self):
        # called directly on job submission and not by the scheduler, so log instead of publishing
        # messages to the scheduler
        output = self.output()
        output.parent.touch()
        logger.info("bundling git repository ...")
        with output.localize("w") as tmp:
            self.bundle(tmp.path)
        logger.info(
            "bundled repository archive, size is {}".format(
                law.util.human_bytes(output.stat().st_size, fmt=True),
            )
        )
