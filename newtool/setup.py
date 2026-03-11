from setuptools import setup

setup(
    name="maker-tool",
    version="7.5.0",
    py_modules=["maker"],
    entry_points={
        'console_scripts': [
            'maker=maker:main',
        ],
    },
)