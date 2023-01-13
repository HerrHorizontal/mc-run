# -*- coding: utf-8 -*-

import os
from subprocess import PIPE
from law.util import interruptable_popen


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
    code, out, error = interruptable_popen("source {}; env".format(source_script_path),
                                            shell=True, 
                                            stdout=PIPE, 
                                            stderr=PIPE
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
        raise RuntimeError(
            'Command {command} returned non-zero exit status {code}!\n'.format(command=executable, code=code)
            + '\tError:\n{}\n'.format(error)
            + '\tOutput:\n{}\n'.format(out) 
        )
    else:
        print('Output:\n{}'.format(out))
    return code, out, error
