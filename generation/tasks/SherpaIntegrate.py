import law
import luigi
import os
import shutil
import multiprocessing  # for cpu_count

from generation.framework.utils import run_command, set_environment_variables

from generation.framework import GenRivetTask

from .SherpaBuild import SherpaConfig, SherpaBuild

from law.logger import get_logger


logger = get_logger(__name__)


class SherpaIntegrate(GenRivetTask):
    """
    Create Sherpa Matrix Elements and Grids for the chosen process.
    """
    ncores = luigi.IntParameter(
        default=int(multiprocessing.cpu_count()/4),
        significant=False,
        description="Number of cores used for the Sherpa integration step."
    )

    def requires(self):
        return {
            "SherpaConfig": SherpaConfig.req(self),
            "SherpaBuild": SherpaBuild.req(self),
        }

    def output(self):
        return self.remote_target("Sherpack.tar.gz")

    def run(self):
        # actual payload:
        print("=======================================================")
        print("Starting integration step to generate integration grids")
        print("=======================================================")

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()

        # set environment variables
        sherpa_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_sherpa.sh")
        )

        # prepare Sherpa for multicore integration
        _sherpa_exec = [
            "mpirun", "-n", str(self.ncores),
            "Sherpa",
            "-f",
            self.input()['SherpaConfig'].path,
            "-e 1",
        ]

        work_dir = os.path.abspath(self.input()['SherpaConfig'].parent.path)

        try:
            run_command(
                _sherpa_exec,
                env=sherpa_env,
                cwd=work_dir,
            )

            # identify files to pack
            output_file = os.path.abspath(os.path.expandvars("$ANALYSIS_PATH/Sherpack.tar.gz"))
            run_file = os.path.join(work_dir, "Run.dat")
            sherpack_includes = []
            sherpack_includes.append(os.path.join(work_dir, "Results.db"))
            sherpack_includes.append(os.path.join(work_dir, "Results.db.bak"))
            sherpack_includes.append(os.path.join(work_dir, "Sherpa_References.tex"))
            from glob import glob
            mig_files = glob(os.path.join(work_dir,"*MIG*.db*"))
            if len(mig_files) == 1:
                sherpack_includes.append(os.path.join(work_dir, mig_files[0]))
            else:
                logger.warning("No matching MIG*.db found! Everything's fine if you are not colliding hadrons... But better check!")
            mpi_file = os.path.join(work_dir,"MPI_Cross_Sections.dat")
            if os.path.isfile(mpi_file):
                sherpack_includes.append(mpi_file)
            else:
                logger.warning("No matching {} found! Everything's fine if you are not colliding hadrons... But better check!".format(mpi_file))
            sherpack_includes.append(os.path.join(work_dir,"Process"))

            # pack and transfer
            old_dir = os.getcwd()
            os.chdir(work_dir)
            run_file = os.path.relpath(run_file)
            for i in range(len(sherpack_includes)):
                sherpack_includes[i] = os.path.relpath(sherpack_includes[i])
            os.system('tar -czf {OUTPUT_FILE} {RUN_FILE} {INCLUDES}'.format(
                OUTPUT_FILE=output_file,
                RUN_FILE=run_file,
                INCLUDES=" ".join(sherpack_includes)
            ))
            os.chdir(old_dir)

        finally:
            # clean up Sherpa outputs regardless of succesful completion
            os.chdir(work_dir)
            for file in sherpack_includes:
                try:
                    os.remove(file)
                except IsADirectoryError:
                    shutil.rmtree(file)
                except Exception as e:
                    raise e
        
        # pack Sherpack for output
        if os.path.exists(output_file):
            output.copy_from_local(output_file)
            os.remove(output_file)   
        else:
            os.system("ls -l")
            raise IOError("Output file '{}' doesn't exist! Abort!".format(output_file))

        print("=======================================================")
