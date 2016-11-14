import os
from setuptools import setup, find_packages

def to_rst (path):
    try:
        from pypandoc import convert
        return convert(path, 'rst')
    except ImportError:
        print("pypandoc module not found, can not convert Markdown to RST")
        return open(path, 'r').read()

def to_array (path):
    with open(path, 'r') as file:
        return [r for r in file.read().split('\n') if r]

setup(
    name='aircox',
    version='0.1',
    license='GPLv3',
    author='bkfox',
    description='Aircox is a radio programs manager that includes tools and cms',
    long_description=to_rst('README.md'),
    url='http://bkfox.net/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=to_array('requirements.txt'),
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)

