import os
import os.path
from setuptools import setup, find_packages

def load_requirements():
    return [req.replace('\n', '') for req in open(os.path.join(os.getcwd(), 'requirements.txt'), 'rt').readlines()]

setup(
    name = 'StarMember'
    , description = "Starstudio Single Sign-on Server."
    , version = '1.0.1'
    , packages = find_packages()
    , install_requires = load_requirements()
)

