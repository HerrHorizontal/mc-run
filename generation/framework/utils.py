# -*- coding: utf-8 -*-

import os
from subprocess import PIPE
from law.util import interruptable_popen

from law.logger import get_logger


logger = get_logger(__name__)


source_env = dict()
for var in ("X509_USER_PROXY", "HOME", "ANALYSIS_PATH", "ANALYSIS_DATA_PATH", "RIVET_ANALYSIS_PATH"):
    try:
        source_env[var] = os.environ[var]
    except KeyError as e:
        logger.warning(f"KeyError: {e}, variable undefined on local host!")


def _convert_env_to_dict(env):
    my_env = {}
    for line in env.splitlines():
        if line.find(" ") < 0 :
            try:
                key, value = line.split("=", 1)
                my_env[key] = value
            except ValueError:
                pass
    return my_env


def set_environment_variables(source_script_path):
    """Creates a subprocess readable environment dict

    Args:
        source_script_path (str): Path to the file sourcing the environment

    Raises:
        RuntimeError: Raised when environment couldn't be sourced

    Returns:
        dict: Environment variables
    """
    code, out, error = interruptable_popen(
        "source {}; env".format(source_script_path),
        shell=True,
        stdout=PIPE,
        stderr=PIPE,
        env=source_env
    )
    if code != 0:
        raise RuntimeError(
            'Sourcing environment from {source_script_path} failed with error code {code}!\n'.format(source_script_path=source_script_path, code=code)
            + 'Output:\n{}\n'.format(out)
            + 'Error:\n{}\n'.format(error)
        )
    my_env = _convert_env_to_dict(out)
    return my_env


def identify_inputfile(filename, config_path, generator):
    if generator == "herwig":
        if(str(config_path) == "" or str(config_path).lower() == "default"):
            _my_input_file = os.path.join(
                "$ANALYSIS_PATH",
                "inputfiles",
                generator,
                "{}.in".format(filename)
            )
        else:
            _my_input_file = os.path.join(
                config_path,
                "{}.in".format(filename)
            )
    elif generator == "sherpa":
        if(config_path == "" or config_path == "default"):
            _my_input_file = os.path.join(
                "$ANALYSIS_PATH",
                "inputfiles",
                generator,
                filename,
                "Run.dat"
            )
        else:
            _my_input_file = os.path.join(
                config_path,
                "Run.dat"
            )
    else:
        raise NotImplementedError("Generator {} unknown!".format(generator))
    return _my_input_file


def identify_setupfile(filepath, generator, mc_setting, work_dir):
    import shutil
    logger.info("Setupfile: {}".format(filepath))
    generator = str(generator)
    if all(filepath != defaultval for defaultval in [None, "None"]):
        setupfile_path = os.path.join(
            os.getenv("ANALYSIS_PATH"),
            "inputfiles",
            generator,
            "setupfiles",
            str(filepath)
        )
    else:
        logger.info("No setupfile given. Trying to identify setupfile via mc_setting ...")
        setupfile_path = os.path.join(
            os.path.expandvars("$ANALYSIS_PATH"),
            "inputfiles",
            generator,
            "setupfiles",
            "{}.txt".format(str(mc_setting))
        )
    if os.path.exists(setupfile_path):
        logger.info("Copy setupfile for executable {} to working directory {}".format(setupfile_path, work_dir))
        # for python3 the next two lines can be merged
        shutil.copy(setupfile_path, work_dir)
        setupfile_path = os.path.basename(setupfile_path)
        # end of merge
        if os.path.exists(setupfile_path):
            return setupfile_path
        else:
            raise IOError("Specified setupfile {} doesn't exist! Abort!".format(setupfile_path))
    else:
        raise IOError("Specified setupfile {} doesn't exist! Abort!".format(setupfile_path))


def run_command(executable, env, *args, **kwargs):
    """Helper function for execution of a command in a subprocess.

    Args:
        executable (List[str]): Command to execute
        env (Dict): Environment for the execution

    Raises:
        RuntimeError: Terminate when subprocess failed. Throw command, error and output streams.

    Returns:
        tuple[int | Any, Any | str, Any | str]: execution code, output string and error string
    """
    command_str = " ".join(executable)
    logger.info('Running command: "{}"'.format(command_str))
    code, out, error = interruptable_popen(
        executable,
        *args,
        stdout=PIPE,
        stderr=PIPE,
        env=env,
        **kwargs
    )
    # if successful return merged YODA file and plots
    if(code != 0):
        import pprint
        pretty_env = pprint.pformat(env,indent=4)
        logger.debug('Env:\n{}'.format(pretty_env))
        logger.error('Output:\n{}'.format(out))
        logger.error('Error:\n{}'.format(error))
        raise RuntimeError(
            'Command {command} returned non-zero exit status {code}!\n'.format(command=executable, code=code)
        )
    else:
        logger.info('Output:\n{}'.format(out))
        if error:
            logger.info('Error:\n{}'.format(error))
    return code, out, error


def check_outdir(outputdict):
    """ensure that the output directory exists"""
    for output in outputdict.values():
        try:
            output.parent.touch()
        except IOError:
            logger.error("Output target {} doesn't exist!".format(output.parent))
            output.makedirs()


def localize_input(input):
    """localize the separate inputs on grid or local storage"""
    logger.info("Input: {}".format(input))
    with input.localize('r') as _file:
        logger.info("\tfile: {}".format(_file.path))
        return _file.path
