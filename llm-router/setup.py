from setuptools import setup, find_packages

setup(
    name="llm-router",
    version="1.0.0",
    author="Developer",
    author_email="developer@example.com",
    description="Intelligent routing system for Language Model requests",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/llm-router",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "openai==1.3.5",
        "anthropic==0.7.0",
        "cohere==5.0.0",
        "requests==2.31.0",
        "numpy==1.24.3",
        "pandas==2.0.3",
        "sqlalchemy==2.0.23",
    ],
    entry_points={
        "console_scripts": [
            "llm-router=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)