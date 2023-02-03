# -*- coding: utf-8 -*-

import os
from subprocess import PIPE
from law.util import interruptable_popen


# source_env = dict()
# for var in ("X509_USER_PROXY", "HOME", "ANALYSIS_PATH", "ANALYSIS_DATA_PATH"):
#     source_env[var]=os.environ[var]

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
    code, out, error = interruptable_popen("source {}; env".format(source_script_path),
                                            shell=True, 
                                            stdout=PIPE, 
                                            stderr=PIPE,
                                            # env=source_env
                                            )
    if code != 0:
        raise RuntimeError(
            'Sourcing environment from {source_script_path} failed with error code {code}!\n'.format(source_script_path=source_script_path, code=code)
            + 'Output:\n{}\n'.format(out)
            + 'Error:\n{}\n'.format(error)
        )
    my_env = _convert_env_to_dict(out)
    return my_env


herwig_env = set_environment_variables(os.path.expandvars(os.path.join("$ANALYSIS_PATH","setup","setup_herwig.sh")))

rivet_env = set_environment_variables(os.path.expandvars(os.path.join("$ANALYSIS_PATH","setup","setup_rivet.sh")))


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
        print('Env:\n')
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(env)
        raise RuntimeError(
            'Command {command} returned non-zero exit status {code}!\n'.format(command=executable, code=code)
            + '\tError:\n{}\n'.format(error)
            + '\tOutput:\n{}\n'.format(out) 
        )
    else:
        print('Output:\n{}'.format(out))
        print('Error:\n{}'.format(error))
    return code, out, error
