from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="whisper_turboapi",
    version="0.1.0",
    author="Kristoffer Vatnehol",
    author_email="kristoffer.vatnehol@gmail.com",
    description="An optimized FastAPI server for OpenAI's Whisper whisper-large-v3-turbo model using MLX turbo optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kristofferv98/whisper_turboapi",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.12.3",
    entry_points={
        "console_scripts": [
            "whisper-turboapi-server=scripts.main:run_server",  # Changed from app to run_server
        ],
    },
)
