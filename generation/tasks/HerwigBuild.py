

import luigi
from luigi.util import inherits
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task, CommonConfig


@inherits(CommonConfig)
class HerwigBuild(Task):
    """
    Gather and compile all necessary libraries and prepare the integration \
    lists for the chosen Matchbox defined in the '[input_file_name].in' file \
    by running 'Herwig build', which will create the Herwig-cache directory \
    and the '[input_file_name].run' file
    """

    # configuration variables
    integration_maxjobs = luigi.Parameter(
        description="Number of individual integration jobs to prepare. \
                Should not be greater than the number of subprocesses."
    )
    config_path = luigi.Parameter(
        significant=False,
        default=os.path.join("$ANALYSIS_PATH","inputfiles"),
        description="Directory where the Herwig config file resides."
    )
    source_script = luigi.Parameter(
        significant=False,
        default=os.path.join("$ANALYSIS_PATH","setup","setup_herwig.sh"),
        description="Path to the source script providing the local Herwig environment to use."
    )


    def output(self):
        return self.remote_target("Herwig-build.tar.gz")

    def run(self):
        # data
        _my_input_file_name = str(self.input_file_name)
        _max_integration_jobs = str(self.integration_maxjobs)
        _config_path = str(self.config_path)

        if(_config_path == "" or _config_path == "default"):
            _my_input_file = os.path.join(
                "$ANALYSIS_PATH",
                "inputfiles",
                "{}.in".format(self.input_file_name)
            )
        else:
            _my_input_file = os.path.join(
                _config_path,
                "{}.in".format(self.input_file_name)
            )

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()

        # actual payload:
        print("=========================================================")
        print("Starting build step to generate Herwig-cache and run file")
        print("=========================================================")

        # set environment variables
        my_env = self.set_environment_variables(source_script_path=self.source_script)

        # run Herwig build step 
        _herwig_exec = ["Herwig", "build"]
        _herwig_args = [
            "--maxjobs={MAXJOBS}".format(MAXJOBS=_max_integration_jobs),
            "{INPUT_FILE}".format(INPUT_FILE=_my_input_file)
        ]

        print('Executable: {}'.format( " ".join(_herwig_exec + _herwig_args)))

        code, out, error = interruptable_popen(
            _herwig_exec + _herwig_args,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save Herwig-cache and run-file as tar.gz
        if(code != 0):
            raise Exception(
                'Error: '
                + error
                + 'Output: '
                + out
                + '\nHerwig build returned non-zero exit status {}'.format(code)
            )
        else:
            cache_dir = os.path.abspath("Herwig-cache")
            output_file = os.path.exists("Herwig-build.tar.gz")

            if(os.path.exists(cache_dir)):
                print('Output: ' + out)
                if not os.listdir(cache_dir):
                    raise LookupError("Herwig cache directory {} is empty!".format(cache_dir))
                os.system('tar -czf {OUTPUT_FILE} {HERWIGCACHE} {INPUT_FILE_NAME}.run'.format(
                    OUTPUT_FILE=output_file,
                    HERWIGCACHE = cache_dir,
                    INPUT_FILE_NAME=_my_input_file_name
                ))
            else:
                raise FileNotFoundError("Something went wrong, Herwig-cache doesn't exist! Abort!")

            if os.path.exists(output_file):
                output.copy_from_local(output_file)
                os.system('rm {OUTPUT_FILE} {INPUT_FILE_NAME}.run'.format(
                    OUTPUT_FILE=output_file,
                    INPUT_FILE_NAME=_my_input_file_name
                ))
            else:
                raise FileNotFoundError("Could not find output file {}!".format(output_file))

        print("=======================================================")

        