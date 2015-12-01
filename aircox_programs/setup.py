import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

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
    install_requires=['django>=1.9.0', 'django-taggit>=0.12.1'],
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ],
)

