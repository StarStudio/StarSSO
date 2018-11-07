import os
import os.path
from setuptools import setup

def load_requirements():
    return [req.replace('\n', '') for req in open(os.path.join(os.getcwd(), 'requirements_checkbot.txt'), 'rt').readlines()]

setup(
    name = 'CheckBot'
    , description = "Checking Dog."
    , version = '1.0.2'
    , packages = [
        'CheckBot'
    ]
    , install_requires = load_requirements()
    , data_files = [
        'requirements_checkbot.txt'
    ]
)
