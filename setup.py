# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in trava_erpnext/__init__.py
from trava_erpnext import __version__ as version

setup(
	name='trava_erpnext',
	version=version,
	description='Trava ERPNext',
	author='Marin',
	author_email='belyerin@ya.ru',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
