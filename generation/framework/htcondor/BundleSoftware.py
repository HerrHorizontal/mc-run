import os
import law
import luigi

law.contrib.load("tasks", "wlcg", "git")


class BundleRepo(law.git.BundleGitRepository, law.tasks.TransferLocalFile):
    replicas = luigi.IntParameter(
        default=10,
        description="number of replicas to generate; default: 10",
    )

    exclude_files = ["tmp", "*~", "*.pyc", ".vscode/", "inputfiles"]

    version = None
    task_namespace = None
    default_store = "$ANALYSIS_PATH/tmp/bundles"

    def get_repo_path(self):
        # required by BundleGitRepository
        return os.environ["ANALYSIS_PATH"]

    def single_output(self):
        repo_base = os.path.basename(self.get_repo_path())
        path = "{}.{}.tgz".format(os.path.basename(repo_base), self.checksum)
        return law.wlcg.WLCGFileTarget(os.path.join("bundles", path), fs="wlcg_fs")

    def get_file_pattern(self):
        path = os.path.expandvars(os.path.expanduser(self.single_output().path))
        return self.get_replicated_path(path, i=None if self.replicas <= 0 else "*")

    def output(self):
        return law.tasks.TransferLocalFile.output(self)

    @law.decorator.safe_output
    def run(self):
        # create the bundle
        bundle = law.LocalFileTarget(is_tmp="tgz")
        self.bundle(bundle)
        # log the size
        self.publish_message(
            "bundled repository archive, size is {}".format(
                law.util.human_bytes(bundle.stat().st_size, fmt=True),
            )
        )
        # transfer the bundle
        self.transfer(bundle)
