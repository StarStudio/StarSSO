import os
import yaml

from .config import LANDeviceProberConfig
from .service.discover import LANDeviceProber


def main():
    config = LANDeviceProberConfig()
    print('LAN Device prober started.')

    if 'API_CFG' not in os.environ:
        print("Environment variable API_CFG not exists.")
        return None
    
    config.FromDict(yaml.load(open(os.environ['API_CFG'], 'rt').read()))

    prober = LANDeviceProber(config)

    return prober.Run()

    

if __name__ == '__main__':
    main() 
