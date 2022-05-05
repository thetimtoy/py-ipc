import re
import setuptools


with open('ipc/__init__.py') as f:
    version = re.findall(r"^__version__ = \'([^']+)\'\r?$", f.read(), re.M)[0]

with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

setuptools.setup(
    name='py-ipc',
    version=version,
    author='thetimtoy',
    license='MIT',
    description='A simple package to facilitate IPC communication in Python',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/thetimtoy/py-ipc',
    project_urls={
        'Bug Tracker': 'https://github.com/thetimtoy/py-ipc/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.7',
)
