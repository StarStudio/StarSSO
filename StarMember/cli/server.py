import argparse
import subprocess
import os
import sys
import gevent
import uuid
import yaml

from traceback import print_exc
from base64 import b64encode

sys.path.append(os.getcwd())

from StarMember.config import Config


class StarSSO:
    parser = argparse.ArgumentParser(
                description = 'Starstudio Single Sign-On Server.'
                , formatter_class = argparse.ArgumentDefaultsHelpFormatter
            )
    
    parser.add_argument('--agent', help = 'Run SSO Server in Agent mode.', action = 'store_true')
    parser.add_argument('--debug', help = 'Debug mode.', action = 'store_true')
    #parser.add_argument('--no-info-shim', help = 'Disable device information resolving when device information is needed. When resolving is disabled, agents will be only used for device discovering.', action = 'store_true')
    parser.add_argument('--register-token', help = 'Token to register network. (Agent mode only)', type = str, default = None)
    parser.add_argument('-c', '--config', help = 'Use specified configure file. Otherwise, configure file specified by Environment Variable API_CFG will be used.', type = str, default = None)
    parser.add_argument('-l', '--listen', help = 'Listen to address for incoming requests.', type = str, default = None)
    parser.add_argument('-p', '--port', help = 'Listen to port for incoming requests.', type = int, default = None)
    #parser.add_argument('--local-publish-port', help = 'Publish port for local network. Default to listening port.', type = int)
    #parser.add_argument('--local-publish-ip', help = 'Publish IP for local network. Default to listening address.', type = str)
    parser.add_argument('--worker-count', help = 'Gunicorn worker instances', type = int, default = 10)
    parser.add_argument('--worker-connections', help = 'Gunicorn worker connections', type = int, default = 1000)
    parser.add_argument('--access-log', help = 'Specified access log file.', type = str, default = None)
    parser.add_argument('--error-log', help = 'Specified error log file', type = str, default = None)
    parser.add_argument('--chdir', help = 'Run server in specified directory.', type = str, default = os.getcwd())
    parser.add_argument('-i', '--interface', help = 'Interface to discover devices. Only for Agent Mode.')
    parser.add_argument('--gunicorn-config', help = 'Gunicorn configure.', type = str)

    def BootstrapAPIServer(self, args, _mode = 'APIServer', _block = True):
        print('Bootstaping StarSSO API Server...')

        envs = os.environ.copy()
        envs['STARSSO_SERVER_MODE'] = _mode

        # Generate WSGI Configure
        conf_tmp = '/tmp/starsso_master_%s.conf' % str(uuid.uuid4()).replace('-', '')
        conf_file = open(conf_tmp, 'wt')
        os.chmod(conf_tmp, 0o600)
        if _mode == 'APIServer':
            conf_dict = yaml.dump(self._cfg.MasterWSGIConfig)
            conf_file.write(conf_dict)
        elif _mode == 'Agent':
            conf_dict = yaml.dump(self._cfg.AgentWSGIConfig)
            if isinstance(args.register_token, str):
                conf_dict['LAN_DEV_REGISTER_TOKEN'] = args.register_token
            conf_file.write(conf_dict)

        conf_file.close()
        envs['API_CFG'] = conf_tmp


        if args.debug is False:
            run_options = self.generate_gunicorn_options(_mode, args)
            if run_options is None:
                return 1
            run_options = ['gunicorn', '-k', 'gevent'] + run_options + ['StarMember.application:app']
        else:
            envs['FLASK_DEBUG'] = "1"
            envs['FLASK_APP'] = 'StarMember.application:app'
            if _mode == 'APIServer':
                run_options = ['flask', 'run'
                                , '-p', str(self._cfg._get_default('apiserver', 'port'))
                                , '-h', str(self._cfg._get_default('apiserver', 'listen'))]
            elif _mode == 'Agent':
                run_options = ['flask', 'run'
                                , '-p', str(self._cfg._get_default('agent', 'port'))
                                , '-h', str(self._cfg._get_default('agent', 'listen'))]
            
    
        if _block is True:
            result = subprocess.run(run_options, env = envs)
            return result
        return subprocess.Popen(run_options, env = envs)

    def _load_configure(self):
        if self._args.config is None:
            cfg_path = os.environ.get('API_CFG', '/etc/starsso/apiserver.yml')
        else:
            cfg_path = self._args.config

        self._cfg = Config(open(cfg_path, 'rt').read())

    
    def BootstrapLANDevice(self, args, _block = True):
        print('Bootstraping LANDevice...')
        config = self.generate_api_configure(args)
        conf_name = '/tmp/starsso_prber_' + str(uuid.uuid4()).replace('-', '')
        conf = open(conf_name, 'wt')
        conf.write(yaml.dump(self._cfg.AgentWSGIConfig))
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
        
    
    def generate_gunicorn_options(self, _mode, args):
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
        if args.access_log is None:
            del MAP_OPT1['access_log']
        if args.error_log is None:
            del MAP_OPT1['error_log']
        for arg, opt in MAP_OPT1.items():
            val = getattr(args, arg, None)
            if val is not None:
                options.append(opt)
                options.append(str(val))
        options.append('-b')
        
        if _mode == 'APIServer':
            options.append('%s:%d' % (self._cfg._get_default('apiserver', 'listen'), self._cfg._get_default('apiserver', 'port')))
        elif _mode == 'Agent':
            options.append('%s:%d' % (self._cfg._get_default('agent', 'listen'), self._cfg._get_default('agent', 'port')))
        return options
        

    def RunServer(self):
        args = StarSSO.parser.parse_args()
        self._args = args
        self._load_configure()
        if args.agent:
            return self.RunAgent(args)
        return self.RunNormal(args)

def Core():
    StarSSO().RunServer()

