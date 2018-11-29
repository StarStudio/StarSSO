import yaml
import os
from os.path import isfile, isdir

def stringwise_representer(dumper, data):
    if isinstance(data, str) and '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', '%s' % data, style = '|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
yaml.add_representer(str, stringwise_representer)


class ConfigureError(Exception):
    pass

class ConfigMap(dict):
    '''
        Base configure class.
    '''
    def __init__(self, _raw = None):
        self._cfg = self.Load(_raw)

    def Load(self, _raw):
        '''
            Load configure.

            :params:
                
        '''
        if _raw is None or len(_raw) < 1:
            return self
        self.update(yaml.load(_raw))
        return self


    def LoadFromFile(self, _path):
        if not isfile(_path):
            if not isdir(os.path.dirname(_path)) and os.path.dirname(_path) != '':
                os.makedirs(os.path.dirname(_path))
            open(_path, 'wt').close()
            return self

        return self.Load(open(_path, 'rt').read())

        

    def DumpToFile(self, _path):
        open(_path, 'wt').write(self.Dump())

    @property
    def raw(self):
        '''
            Dump application metadata to bytes.
        '''
        return yaml.dump(dict(self)).encode('utf8')


    @raw.setter
    def raw(self, _raw):
        '''
            Load application metadata from raw bytes.
        '''
        if not isinstance(_raw, bytes):
            if _raw is None:
                self.clear()
                return
            raise ValueError('Cannot apply raw content to ConfigMap')
        raw_string = _raw.decode('utf8')
        config_map = yaml.load(raw_string)
        self.clear()
        self.update(config_map)
            
        
    def Dump(self):
        '''
            Dump configure.
        '''
        
        return yaml.dump(dict(self), default_flow_style = False)

    def _get_default(self, *args, **kwargs):
        '''
            Get value from specified dict path.

            :example:
                _get_default('key1', 'key2', ..., 'keyN', default = 'Value')

                This call of _get_default tries to get self['key1']['key2']...['keyN'].
                If any key through the path doesn't exists, return 'Value'.
                
                The param 'defualt' is optional.
        '''
        prev = None
        this = self
        set_default = False
        for key in args:
            if key not in this:
                this[key] = {}
                set_default = True
            prev = this
            this = this.get(key)
        if set_default:
            this = kwargs.get('default', None)
            if this is None:
                this = self.DEFAULT_VALUES.get(tuple(args), None)
            prev[key] = this
        return this

    def _set_default(self, *args, **kwargs):
        '''
            Set value to specified dict path.

            :example:
                _set_default('key1', 'key2', ..., 'keyN', default = 'Value')

                This call of _set_default set self['key1']['key2']...['keyN'] = 'Value'.
        '''
        prev = None
        this = self
        for key in args:
            if key not in this:
                this[key] = {}
            prev = this
            this = this.get(key)
        prev[args[-1]] = kwargs['default']


    def _delete_key(self, *args):
        '''
            Delete value of specified dict path.

            :exmaple:
                _delete_key('key1', 'key2', ..., 'keyN')

                It deletes self['key1']['key2']...['keyN'] and any empty map.
        '''
        stack = []
        this = self
        reach_tail = True
        for key in args[:-1]:
            if key not in this:
                reach_tail = False
                break
            stack.append((this, key))
            this = this.get(key)

        # Delete key
        if reach_tail and args[-1] in this:
            del this[args[-1]]

        # Delete all empty maps.
        while stack:
            prev, this_key = stack.pop()
            if not this:
                del prev[this_key]
            this = prev
                
        
