from setuptools import setup

setup(
    name="maker-tool",
    version="7.7.0",
    description="The complete Maker CLI Suite",
    py_modules=["maker"],
    entry_points={
        'console_scripts': [
            'maker=maker:main',
        ],
    },
)