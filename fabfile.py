# -*- coding: utf-8 -*-
"""
Fabric SDLC Deployment

Runs in Paralell

- Required
    - SSH Key(s) for Server(s)
    - An ~/.ssh/config file with your settings, an Example (You don't have to nest details with tabs, I only prefer it):
        # --- start example
        Host dev01 # (Any name you want)
            HostName 22.22.22.21        # DNS or IP
            Port 3002                   # 22 is default, omit if not custom
            User yourlogin              # Your SSH Login Username
            IdentityFile ~/.ssh/id_rsa  # Your SSH Private Key to Server, omit if not used
            ForwardAgent yes            # Uses your ssh-agent stored keys remotely for git to pull
                                        # $ ssh-add ~/.ssh/yourkey
        # --- end example
    - Server Paths Already Setup
    - Git Repo Name must match the Path Name, eg:
        - Repo: my-story.git
        - /path/to/my-story/ (live/prod)
        - /path/to/develop.my-story/ (auto-prefixed)
    - (Not Recommended) Remote sudo permissions only if running certain commands
- Install: pip install fabric
- Configure: the variables below
"""

import sys
import os
from fabric.api import *
from fabric.colors import red, green, yellow, cyan
from fabric.contrib import files.exists
from fabric.operations import require

"""
Yes you can use .fabricrc but it forces the env.vars immediately,
so i used pyyaml for cleaner config..

pip install -r requitements.txt
"""
env.config_file = 'fabric.config.yml
env.use_ssh_config = True
# env.ssh_config_path = '~/.ssh/'

"""
- Name of GIT repo (without .git)
- Name of FOLDER on HOST
"""
PROJECT = 'jream.network'

"""
- Path to project location.
- The %s is to prefix with subfolder names:
    - web.com, stage.web.com, test.web.com, etc.
"""
PROJECT_PATH = "/var/www/%s/"

"""
- Path to local project.
- This may not affect a whole lot besides specified: EXTRA_*_COMMANDS
"""
PROJECT_LOCAL_PATH = "~/home/projects/%s/"

"""
- (Optional) Flush File Cache
- If not exists and specified, it is ignored.
"""
PROJECT_CACHE_PATH = 'var/cache/twig/'

"""
- (Optional) Add Extra Commands
- Occurs AFTER the Deployment
- Example: clear system redis cache, clear SQL cache
"""
EXTRA_OS_COMMANDS = [
    # Flush all Redis DB's on Host(s)
    # 'redis-cli flushall',
    # Example: Flush a Single Redis DB on Host(s)
    #'redis-cli -n 1 flushdb',
]

"""
- (Optional) Run commands from your project root
- Occurs AFTER the Deployment
- Example: pip update, composer or npm updates.
    - or even set file permissions or facl if you wanted.
"""
EXTRA_PATH_COMMANDS = [
    # Update Composer Dependencies
    "composer update --prefer-dist --no-dev --optimize-autoloader",
    # Example: update pip packages
    #"pip install -r requirements.txt"
]

"""
- SDLC: The four Main Segments, use what you need.
    - LIVE: prod, production
    - DEV: develop, development
    - STAGE: staging
    - TEST: testing
- Must be ONE or MANY hosts to deploy to (Your Choice)
- The SAME host CAN be used, the GIT branch for staging will prefix
    a staging.folder.name, the LIVE has no suffix.
"""
LIVE_HOSTS = ['123.123.123.132',]
STAGE_HOSTS = ['123.123.123.132',]
TEST_HOSTS = ['123.123.123.132',]
DEV_HOSTS = ['123.123.123.132',]
LOCAL_HOSTS = ['127.0.0.1',]

"""
- Default Private Key for SSH
- You can use one, or different ones depending on your server configuration
"""
PRIVATE_KEY_DEFAULT = "~/.ssh/id_rsa"
LIVE = PRIVATE_KEY_DEFAULT
STAGE = PRIVATE_KEY_DEFAULT
TEST = PRIVATE_KEY_DEFAULT
DEV = PRIVATE_KEY_DEFAULT
LOCAL = PRIVATE_KEY_DEFAULT
# key_filename


PARAMS_LIVE = dict(
    hosts=LIVE_HOSTS,
    path=PROJECT_PATH % PROJECT,
    branch='master',
    cmds=dict(
        os=EXTRA_OS_COMMANDS,
        path=EXTRA_PATH_COMMANDS
    )
),

PARAMS_STAGE = dict(
    hosts=STAGE_HOSTS,
    path=PROJECT_PATH % 'staging.' + PROJECT,
    branch='staging',
    cmds=dict(
        os=EXTRA_OS_COMMANDS,
        path=EXTRA_PATH_COMMANDS
    )
),

PARAMS_TEST = dict(
    hosts=TEST_HOSTS,
    path=PROJECT_PATH % 'testing.' + PROJECT,
    branch='testing',
    cmds=dict(
        os=EXTRA_OS_COMMANDS,
        path=EXTRA_PATH_COMMANDS
    )
),

PARAMS_DEV = dict(
    hosts=DEV_HOSTS,
    path=PROJECT_PATH % 'develop.' + PROJECT,
    branch='develop',
    cmds=dict(
        os=EXTRA_OS_COMMANDS,
        path=EXTRA_PATH_COMMANDS
    )
),

PARAMS_LOCAL = dict(
    hosts=LOCAL_HOSTS,
    path=PROJECT_LOCAL_PATH % PROJECT,
    branch=False,
    cmds=dict(
        os=EXTRA_OS_COMMANDS,
        path=EXTRA_PATH_COMMANDS
    )
),

"""
[!] Error Prevention
    Ensure a trailing slash is at the end of the cache path.
"""
if PROJECT_CACHE_PATH[-1:] != '/':
    PROJECT_CACHE_PATH += '/'


def set_stage(stage_name):
    """Sets env.path, env.branch, etc variables
    """
    env.stage = stage_name

    """
    [!] Error Prevention
    Do not run a with 0 hosts.
    """
    if not stage_name.hosts:
        sys.exit("Stage: {0} has no Host, nothing will be run.".format(stage_name))

    # @@TODO
    env.key_filename = "~/.ssh/id_rsa"
    for option, value in STAGES[env.stage].items():
        setattr(env, option, value)

"""
- Tasks to associate with the Deployment
- Usage: fab test deploy
         fab dev deploy
"""
@task
def live():
    """Live Server"""
    set_stage(PARAMS_LIVE)

@task
def stage():
    """Stage Environment."""
    set_stage(PARAMS_STAGE)

@task
def test():
    """Test Environment."""
    set_stage(PARAMS_TEST)

@task
def dev():
    """Develop Environment."""
    set_stage(PARAMS_DEV)


@task
def localhost():
    """Localhost."""
    set_stage(PARAMS_LOCAL)

# Aliases
@task
def prod():
    """Alias: for Live"""
    live()

def develop():
    """Alias: for Dev"""
    dev()

# ------------------------------------------------------------------------------
# Server
# ------------------------------------------------------------------------------

@task
@parallel
def rmcache():
    """Removes Cache
    """
    if not files.exists(PROJECT_CACHE_PATH, use_sudo=False, verbose=False):


    commands = [
        "redis-cli flushall",
        "find {0} -type f -name '*.volt.php' -exec rm -rf {{}} +".format(PROJECT_CACHE_PATH),
        "find {0} -type f -name '*.volt_e_.php' -exec rm -rf {{}} +".format(PROJECT_CACHE_PATH),
        "rm -rf {0}*%%.php".format(PROJECT_CACHE_PATH),
        "rm -rf {0}*.volt.php".format(PROJECT_CACHE_PATH)
    ]
    if env.stage is 'local':
        for cmd in commands:
            local(cmd)
    else:
        with cd(env.path):
            for cmd in commands:
                run(cmd)


@task
@parallel
def composer():
    """Runs a composer update
    """
    response = []
    with cd(env.path):
        response.append( run("composer update --prefer-dist --no-dev --optimize-autoloader") )

@task
@parallel
def deploy():
    """Deploy the project to remote host
    """
    require('stage', provided_by=(live, stage, test, dev,))
    response = []
    with cd(env.path):
        response.append( run('git checkout {0}'.format(env.branch)) )
        response.append( run('git pull origin {0}'.format(env.branch)) )

        # @TODO extra cmds

