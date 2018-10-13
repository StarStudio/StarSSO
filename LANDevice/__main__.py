import os

from .config import LANDeviceProberConfig
from .service.discover import LANDeviceProber


def main():
    config = LANDeviceProberConfig()
    print('LAN Device prober started.')

    if 'LAN_DEV_PROBER_CONFIG' not in os.environ:
        print("Environment variable LAN_DEV_PROBER_CONFIG not exists.")
        return None
    else:
        config.FromEnv('LAN_DEV_PROBER_CONFIG')

    prober = LANDeviceProber(config)

    return prober.Run()

    

if __name__ == '__main__':
    main() 
