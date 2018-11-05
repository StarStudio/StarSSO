#! /bin/python
import argparse
import subprocess
import os
import sys


parser = argparse.ArgumentParser(description = 'Starstudio Single Sign-On Server.')
parser.add_argument('--agent', help = 'Run SSO Server in Agent mode.', action = 'store_true')
parser.add_argument('-c', '--config', help = 'Use specified configure file. Otherwise, configure file specified by Environment Variable API_CFG will be used.', type = str)
parser.add_argument('-l', '--listen', help = 'Listen to address for incoming requests.', type = str, default = '0.0.0.0')
parser.add_argument('-p', '--port', help = 'Listen to port for incoming requests.', type = int, default = 80)
parser.add_argument('--worker-count', help = 'Gunicorn worker instances', type = int, default = 10)
parser.add_argument('--worker-connections', help = 'Gunicorn worker connections', type = int, default = 1000)
parser.add_argument('--access-log', help = 'Specified access log file.', type = str, default = '/var/log/starsso/access.log')
parser.add_argument('--error-log', help = 'Specified error log file', type = str, default = '/var/log/starsso/error.log')
parser.add_argument('--disable-access-log', help = 'Disable access logging.', action = 'store_true')
parser.add_argument('--disable-error-log', help = 'Disable error logging.', action = 'store_true')
parser.add_argument('--chdir', help = 'Run server in specified directory.', type = str, default = os.getcwd())
parser.add_argument('-i', '--interface', help = 'Interface to discover devices. Only for Agent Mode.')
parser.add_argument('--gunicorn-config', help = 'Gunicorn configure.', type = str)
parser.add_argument('--api-config', help = 'APIServer configure', type = str)


def BootstrapAPIServer(args, _mode = 'APIServer', _block = True):
    print('Bootstaping StarSSO API Server...')
    gunicorn_options = generate_gunicorn_options(args)
    if gunicorn_options is None:
        return 1
    gunicorn_options = ['gunicorn'] + gunicorn_options + ['StarMember:app']
    envs = os.environ.copy()
    if args.api_config is not None:
        envs['API_CFG'] = args.api_config
    envs['STARSSO_SERVER_MODE'] = _mode

    if _block is True:
        result = subprocess.run(gunicorn_options, env = envs)
        return result


def RunAgent(args):
    BootstrapAPIServer(args, _block = False)


def RunNormal(args):
    result = BootstrapAPIServer(args) 
    return result.returncode
    

def generate_gunicorn_options(args):
    options = []
    if args.gunicorn_config is not None:
        if not os.path.isfile(args.gunicorn_config):
            print('Gunicorn file not found: %s' % args.gunicorn_config)
            return None
    MAP_OPT1 = {
        'worker_count': '-w'
        , 'worker_connections': '--worker-connections'
        , 'access_log': '--access-logfile'
        , 'error_log': '--error-logfile'
        , 'gunicorn_config': '-c'
        , 'chdir': '--chdir'
    }
    if args.disable_access_log:
        del MAP_OPT1['access_log']
    if args.disable_error_log:
        del MAP_OPT1['error_log']
    for arg, opt in MAP_OPT1.items():
        val = getattr(args, arg, None)
        if val is not None:
            options.append(opt)
            options.append(str(val))
    options.append('-b')
    options.append('%s:%d' % (args.listen, args.port))
    return options 
    

def RunServer():
    args = parser.parse_args()
    if args.agent:
        return RunAgent(args)
    return RunNormal(args)

RunServer()
