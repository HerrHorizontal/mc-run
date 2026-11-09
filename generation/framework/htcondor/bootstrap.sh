#!/usr/bin/env bash

# Bootstrap file that is executed by remote jobs submitted by law to set up the environment.
# So-called render variables, denoted by "{{name}}", are replaced with variables
# configured in the remote workflow tasks.

# Bootstrap function for standalone htcondor jobs, i.e., each job unpacks the repository bundle
# shipped with its input sandbox to have a standalone environment, independent of the submitting one.
# The setup script of the repository is sourced with a few environment variables being set before,
# tailored for remote jobs.
bootstrap_htcondor_standalone() {
    export LCG_DIR="/cvmfs/grid.cern.ch/alma9-ui-test"
    local grid_ui
    grid_ui="${LCG_DIR}/etc/profile.d/setup-alma9-test.sh"

    # set env variables
    local BASE_DIR="${PWD}"
    export HOME="${PWD}"
    export ANALYSIS_PATH="${BASE_DIR}/repo"

    # when gfal-* executables are not available, source the lcg dir
    if ! command -v "gfal-ls" &> /dev/null && [ -n "${LCG_DIR}" ] && [ -d "${LCG_DIR}" ]; then
        source "$grid_ui"
    fi

    # unpack the repo bundle shipped with the input sandbox of the job
    mkdir -p "${ANALYSIS_PATH}" || return "$?"
    tar -xzf "${BASE_DIR}/{{repo_bundle}}" -C "${ANALYSIS_PATH}" || return "$?"
    echo "Analysis repo setup done."

    # source the repo setup
    source "${ANALYSIS_PATH}/setup.sh" "default" || return "$?"

    return "0"
}

export MCRUN_REMOTE=1
bootstrap_htcondor_standalone "$@"
