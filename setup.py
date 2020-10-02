from setuptools import setup, find_packages

setup(
    name="pytest-eye",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    version='0.0.2',
    description='Pytest plugin for Selenium approval testing',
    author='Timofey Dolganov',
    author_email='kaor.bp@gmail.com',
    url='https://github.com/kaor4bp/pytest-eye',

    package_data={
        '': ['*.js']
    },

    # the following makes a plugin available to pytest
    entry_points={
        'pytest11': [
            'pytest-eye = eye.plugin',
        ],
    },
    install_requires=[
        'numpy>=1.18.1',
        'pillow>=7.0.0',
        'selenium>=3.141.0',
        'pytest>=6.0.1'
    ]
)
