import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vquest",
    version="0.0.1",
    author="Jesse Connell",
    author_email="jesse@ressy.us",
    description="Automate IMGT V-QUEST usage on imgt.org",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ressy/vquest",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
