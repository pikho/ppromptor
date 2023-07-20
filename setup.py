import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="ppromptor",
    version=find_version("ppromptor", "__init__.py"),
    url="https://github.com/pikho/ppromptor",
    author="Pikho Tan",
    author_email="pikho.tan[at]gmail.com",
    description="A framework for automatic prompt generation",
    packages=find_packages(exclude=["llms"]),
    packages=find_packages(exclude=["*_private_llms*"]),
    package_data={"ppromptor": ["examples/*"]},
    scripts=['scripts/ppromptor-main.py'],
    install_requires=[
        "langchain", "loguru", "dataclasses_json",
        "torch", "auto_gptq", "requests", "openai", "transformers",
        "sqlalchemy"
    ],
    include_package_data=True,
    extras_require={
        'docs': [
            'sphinx'
        ],
        'test': [
            'pytest'
        ]
    },
    python_requires=">=3.10",
)
