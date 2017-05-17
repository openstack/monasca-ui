#!/usr/bin/env bash

# Constraint file contains this package version pin that is in conflict
# with installing the package from source. We should replace the version pin in
# the constraints file before applying it for from-source installation.

ZUUL_CLONER=/usr/zuul-env/bin/zuul-cloner
BRANCH_NAME=master
PACKAGE_NAME=monasca-ui
requirements_installed=$(echo "import openstack_requirements" | python 2>/dev/null ; echo $?)

function install_client_depends_on() {
    local client_location
    if [ -x "$ZUUL_CLONER" ]; then
        # install in gate environment
        pushd $mydir
        $ZUUL_CLONER --cache-dir \
            /opt/git \
            git://git.openstack.org \
            openstack/python-monascaclient
        cd openstack/python-monascaclient
        echo "Using python-monascaclient $(git log -n 1 --oneline)"
        client_location="file://$PWD#egg=python_monascaclient"
        popd
    else
        echo "Using python-monascaclient@master"
        client_location="git+https://git.openstack.org/openstack/python-monascaclient@master#egg=python_monascaclient"
    fi
    edit-constraints $localfile -- "python-monascaclient" "$client_location"
    $install_cmd -U "$client_location"
}

set -e

git config --global url.https://git.openstack.org/.insteadOf git://git.openstack.org/

CONSTRAINTS_FILE=$1
shift

install_cmd="pip install"
mydir=$(mktemp -dt "$PACKAGE_NAME-tox_install-XXXXXXX")
trap "rm -rf $mydir" EXIT
localfile=$mydir/upper-constraints.txt
if [[ $CONSTRAINTS_FILE != http* ]]; then
    CONSTRAINTS_FILE=file://$CONSTRAINTS_FILE
fi
curl $CONSTRAINTS_FILE -k -o $localfile
install_cmd="$install_cmd -c$localfile"

if [ $requirements_installed -eq 0 ]; then
    echo "ALREADY INSTALLED" > /tmp/tox_install.txt
    echo "Requirements already installed; using existing package"
elif [ -x "$ZUUL_CLONER" ]; then
    echo "ZUUL CLONER" > /tmp/tox_install.txt
    pushd $mydir
    $ZUUL_CLONER --cache-dir \
        /opt/git \
        --branch $BRANCH_NAME \
        git://git.openstack.org \
        openstack/requirements
    cd openstack/requirements ; $install_cmd -e . ; cd -
    popd
else
    echo "PIP HARDCODE" > /tmp/tox_install.txt
    if [ -z "$REQUIREMENTS_PIP_LOCATION" ]; then
        REQUIREMENTS_PIP_LOCATION="git+https://git.openstack.org/openstack/requirements@$BRANCH_NAME#egg=requirements"
    fi
    $install_cmd -U -e ${REQUIREMENTS_PIP_LOCATION}
fi

# This is the main purpose of the script: Allow local installation of
# the current repo. It is listed in constraints file and thus any
# install will be constrained and we need to unconstrain it.
edit-constraints $localfile -- $PACKAGE_NAME "-e file://$PWD#egg=$PACKAGE_NAME"
install_client_depends_on

$install_cmd -U $*
exit $?
