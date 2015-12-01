import os
from setuptools import setup

cwd = os.path.dirname(__file__)
with open(os.path.join(cwd, 'README.md')) as readme:
    README = readme.read()

with open(os.path.join(cwd, 'requirements.txt')) as requirements:
    REQUIREMENTS = requirements.read()
    REQUIREMENTS = [r for r in REQUIREMENTS.split('\n') if r]

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='aircox_programs',
    version='0.1',
    license='GPLv3',
    author='lordblackfox',
    description='Aircox core application: programs and stations management',
    long_description=README,
    url='http://bkfox.net/',
    include_package_data=True,
    install_requires=REQUIREMENTS,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)

