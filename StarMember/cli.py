#! /bin/python
import argparse
import subprocess
import os
import sys
import gevent
import uuid
from traceback import print_exc


parser = argparse.ArgumentParser(
            description = 'Starstudio Single Sign-On Server.'
            , formatter_class = argparse.ArgumentDefaultsHelpFormatter
        )

parser.add_argument('--agent', help = 'Run SSO Server in Agent mode.', action = 'store_true')
parser.add_argument('--register-token', help = 'Token to register network.', type = str)
parser.add_argument('--network-id-file', help = 'File to save/load network id', type = str)
parser.add_argument('-c', '--config', help = 'Use specified configure file. Otherwise, configure file specified by Environment Variable API_CFG will be used.', type = str)
parser.add_argument('-l', '--listen', help = 'Listen to address for incoming requests.', type = str, default = '0.0.0.0')
parser.add_argument('-p', '--port', help = 'Listen to port for incoming requests.', type = int, default = 80)
parser.add_argument('--local-publish-port', help = 'Publish port for local network. Default to listening port.', type = int)
parser.add_argument('--local-publish-ip', help = 'Publish IP for local network. Default to listening address.', type = str)
parser.add_argument('--worker-count', help = 'Gunicorn worker instances', type = int, default = 10)
parser.add_argument('--worker-connections', help = 'Gunicorn worker connections', type = int, default = 1000)
parser.add_argument('--access-log', help = 'Specified access log file.', type = str)
parser.add_argument('--error-log', help = 'Specified error log file', type = str)
parser.add_argument('--chdir', help = 'Run server in specified directory.', type = str, default = os.getcwd())
parser.add_argument('-i', '--interface', help = 'Interface to discover devices. Only for Agent Mode.')
parser.add_argument('--gunicorn-config', help = 'Gunicorn configure.', type = str)

class StarSSO:

    def BootstrapAPIServer(self, args, _mode = 'APIServer', _block = True):
        print('Bootstaping StarSSO API Server...')
        gunicorn_options = self.generate_gunicorn_options(args)
        if gunicorn_options is None:
            return 1
        gunicorn_options = ['gunicorn', '-k', 'gevent'] + gunicorn_options + ['StarMember:app']
        envs = os.environ.copy()
        if args.config is not None:
            envs['API_CFG'] = args.config
        envs['STARSSO_SERVER_MODE'] = _mode
    
        if _block is True:
            result = subprocess.run(gunicorn_options, env = envs)
            return result
        return subprocess.Popen(gunicorn_options, env = envs)
    
    
    def BootstrapLANDevice(self, args, _block = True):
        print('Bootstraping LANDevice...')
        config = self.generate_api_configure(args)
        conf_name = os.path.join('/tmp/', str(uuid.uuid4()).replace('-', ''))
        conf = open(conf_name, 'wt')
        if args.config is not None:
            try:
                ori = open(args.config, 'rt').read()
            except FileNotFoundError as e:
                print('Cannot found configure file: %s' % args.config, file = sys.stderr)
                raise e
            conf.write(ori)
            conf.write('\n')
        conf.write(config)
        envs = os.environ.copy()
        run_args = ['python', '-m', 'StarMember.agent']
        if args.config is not None:
            envs['API_CFG'] = conf_name
        if _block is True:
            result = subprocess.run(run_args, env = envs)
            return result
        return subprocess.Popen(run_args, env = envs)
            
    
    def RunAgent(self, args):
        def wait_fibre(popen):
            popen.wait()

        api_proc = self.BootstrapAPIServer(args, _mode = 'Agent', _block = False)
        landevice_proc = self.BootstrapLANDevice(args, _block = False)
        gevent.wait([
                    gevent.spawn(wait_fibre, api_proc)
                    , gevent.spawn(wait_fibre, landevice_proc)
                ], count = 1)

        api_proc.terminate()
        landevice_proc.terminate()
        print('API Server exit with: %d' % api_proc.returncode)
        print('Device prober exit with: %d' % landevice_proc.returncode)
        if api_proc.returncode != 0 or api_proc.returncode != 0:
            return 2

        
    def generate_api_configure(self, args):
        MAP_OPTS = {
            'access_log': 'ACCESS_LOG'
            , 'error_log': 'ERROR_LOG'
        }
        config = '\n'
        for arg, opt in MAP_OPTS.items():
            val = getattr(args, arg, None)
            if val is not None:
                config += '%s=\'%s\'\n' % (opt, val)
        return config
            

    def RunNormal(self, args):
        result = self.BootstrapAPIServer(args)
        return result.returncode
        
    
    def generate_gunicorn_options(self, args):
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
        

    def RunServer(self):
        args = parser.parse_args()
        if args.agent:
            return self.RunAgent(args)
        return self.RunNormal(args)


StarSSO().RunServer()
