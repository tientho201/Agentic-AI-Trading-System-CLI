from setuptools import setup, find_packages
from typing import List

def requirements() -> List[str]:
    """
    
    """
    requirements_ls : List[str] = []
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and line.strip() != "-e .":
                    requirements_ls.append(line.strip())
    except Exception as e:
        raise e
    return requirements_ls

setup(
    name="src",
    version="0.0.1",
    author="tientho201",
    author_email="tientho2012004@gmail.com",
    packages=find_packages(),
    install_requires=requirements(),
)