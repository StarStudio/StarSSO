import os
import os.path
from setuptools import setup, find_packages

def load_requirements():
    return [req.replace('\n', '') for req in open(os.path.join(os.getcwd(), 'requirements.txt'), 'rt').readlines()]

setup(
    name = 'StarSSO'
    , description = "Starstudio Single Sign-on Server."
    , version = '1.0.2'
    #, packages = find_packages(exclude=['LANDevice', 'LANDevice.*'])
    , packages = [
        'StarMember'
    ] + [ 'StarMember.' + sub_pack for sub_pack in find_packages(where = 'StarMember')]
    , install_requires = load_requirements()
    , data_files = [
        'requirements.txt'
    ]
    , entry_points = {
        'console_scripts': [
            'starsso-server = StarMember.cli:Core'
            , 'starsso-manage = StarMember.cli:Manage'
        ]
    }
)

