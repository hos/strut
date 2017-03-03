from setuptools import setup, find_packages
from os import path
from setuptools.extension import Extension
# from Cython.Build import cythonize


here = path.abspath(path.dirname(__file__))


setup(
    name = "strut",

    version = "0.0",

    description = "STRUctural Toolkit",

    author = "H. Onur Solmaz",

    author_email = "onursolmaz@gmail.com",

    packages = find_packages(exclude=["contrib", "docs", "tests"]),

    extras_require = {
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },

    # package_data={
    #     "sample": ["package_data.dat"],
    # },

    # data_files=[("my_data")],

    install_requires = {
        "numpy",
        "scipy",
        "python-dateutil",
        "meshpy",
    },

    # ext_modules = cythonize("strut/armfunctions.pyx"),

    entry_points = {
        "console_scripts": [
            # "strut_app=strut.bin.strut_app:__main__",
        ],
    },
)



