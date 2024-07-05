#!/usr/bin/env bash

# Bootstrap file that is executed by remote jobs submitted by law to set up the environment.
# So-called render variables, denoted by "{{name}}", are replaced with variables
# configured in the remote workflow tasks.

# Bootstrap function for standalone htcondor jobs, i.e., each jobs fetches a software and repository
# code bundle and unpacks them to have a standalone environment, independent of the submitting one.
# The setup script of the repository is sourced with a few environment variables being set before,
# tailored for remote jobs.
bootstrap_htcondor_standalone() {
    # set env variables
    local BASE_DIR="${PWD}"
    export HOME="${PWD}"
    export LCG_DIR="/cvmfs/grid.cern.ch/alma9-ui-test"
    export ANALYSIS_PATH="${BASE_DIR}/repo"

    # source the law wlcg tools, mainly for law_wlcg_get_file
    source "{{wlcg_tools}}" "" || return "$?"

    # when gfal-* executables are not available, source the lcg dir
    if ! law_wlcg_check_executable "gfal-ls" "silent" && [ -n "${LCG_DIR}" ] && [ -d "${LCG_DIR}" ]; then
        source "${LCG_DIR}/etc/profile.d/setup-alma9-test.sh" ""
    fi

    # load the repo bundle
    (
        mkdir -p "${ANALYSIS_PATH}"
        cd "${ANALYSIS_PATH}" || exit "$?"
        law_wlcg_get_file "{{repo_uris}}" '{{repo_pattern}}' "${PWD}/repo.tgz" || return "$?"
        tar -xzf "repo.tgz" || return "$?"
        rm "repo.tgz"
        echo "Analysis repo setup done."
    )

    # source the repo setup
    source "${ANALYSIS_PATH}/setup.sh" "default" || return "$?"

    return "0"
}

export MCRUN_REMOTE=1
bootstrap_htcondor_standalone "$@"
