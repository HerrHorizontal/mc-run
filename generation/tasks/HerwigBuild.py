

import luigi
from luigi.util import inherits
import os, shutil

from subprocess import PIPE
from generation.framework.utils import run_command, identify_setupfile, identify_inputfile, set_environment_variables
from generation.framework.tasks import Task, GenerationScenarioConfig


@inherits(GenerationScenarioConfig)
class HerwigBuild(Task):
    """
    Gather and compile all necessary libraries and prepare the integration \
    lists for the chosen Matchbox defined in the '[input_file_name].in' file \
    by running 'Herwig build', which will create the Herwig-cache directory \
    and the '[input_file_name].run' file
    """

    mc_generator = "herwig"

    # configuration variables
    integration_maxjobs = luigi.Parameter(
        description="Number of individual integration jobs to prepare. \
                Should not be greater than the number of subprocesses."
    )
    config_path = luigi.Parameter(
        significant=True,
        default="default",
        description="Directory where the Herwig config file resides. Default transaltes to `inputfiles/herwig/`."
    )

    setupfile = luigi.Parameter()


    def remote_path(self,*path):
        if self.mc_setting == "PSoff":
            parts = (self.__class__.__name__,self.input_file_name, self.mc_setting, ) + path
            return os.path.join(*parts)
        else:
            parts = (self.__class__.__name__, self.input_file_name,) + path
            return os.path.join(*parts)

    def output(self):
        return self.remote_target("Herwig-build.tar.gz")

    def run(self):
        # data
        input_file_name = str(self.input_file_name)
        _max_integration_jobs = str(self.integration_maxjobs)
        _config_path = str(self.config_path)

        _my_input_file = identify_inputfile(input_file_name, _config_path, self.mc_generator)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()

        # actual payload:
        print("=========================================================")
        print("Starting build step to generate Herwig-cache and run file")
        print("=========================================================")

        herwig_env = set_environment_variables(os.path.expandvars(os.path.join("$ANALYSIS_PATH","setup","setup_herwig.sh")))
        # run Herwig build step 
        _herwig_exec = ["Herwig", "build"]
        _herwig_args = [
            "--maxjobs={MAXJOBS}".format(MAXJOBS=_max_integration_jobs),
            "{INPUT_FILE}".format(INPUT_FILE=_my_input_file)
        ]
        if self.mc_setting == "PSoff":
            _setupfile_path = identify_setupfile(self.setupfile, self.mc_generator, self.mc_setting, os.getcwd())
            _herwig_args = ["--setupfile={SETUPFILE}".format(SETUPFILE=_setupfile_path)] + _herwig_args

        print('Executable: {}'.format( " ".join(_herwig_exec + _herwig_args)))

        try:
            run_command(_herwig_exec+_herwig_args, env=herwig_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
        except RuntimeError as e:
            output.remove()
            raise e

        cache_dir = os.path.abspath(os.path.expandvars("$ANALYSIS_PATH/Herwig-cache"))
        output_file = os.path.abspath(os.path.expandvars("$ANALYSIS_PATH/Herwig-build.tar.gz"))
        run_file = os.path.abspath(os.path.expandvars("$ANALYSIS_PATH/{}.run".format(input_file_name)))

        if(os.path.exists(cache_dir) and os.path.isfile(run_file)):
            print("Checking {} ...".format(cache_dir))
            if not os.listdir(cache_dir):
                raise LookupError("Herwig cache directory {} is empty!".format(cache_dir))
            print("Tarring {0} and {1} into {2} ...".format(cache_dir,run_file,output_file))
            os.system('tar -czf {OUTPUT_FILE} {HERWIGCACHE} {INPUT_FILE_NAME}.run'.format(
                OUTPUT_FILE=output_file,
                HERWIGCACHE = os.path.relpath(cache_dir),
                INPUT_FILE_NAME=input_file_name
            ))
        else:
            raise IOError("Something went wrong, Herwig-cache or run-file doesn't exist! Abort!")

        if os.path.exists(output_file):
            output.copy_from_local(output_file)
            os.remove(output_file)
            os.remove(run_file)
            shutil.rmtree(cache_dir)
        else:
            raise IOError("Could not find output file {}!".format(output_file))

        print("=======================================================")

        
