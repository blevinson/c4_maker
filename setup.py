from setuptools import setup, find_packages

setup(
    name='c4_maker',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'annotated-types',
        'anyio',
        'certifi',
        'distro',
        'exceptiongroup',
        'h11',
        'httpcore',
        'httpx',
        'idna',
        'openai<1.31.65',
        'pydantic',
        'pydantic_core',
        'python-dotenv',
        'sniffio',
        'tqdm',
        'typing_extensions',
        'pystructurizr',  # Make sure you specify the version you want to depend on
        # ... any other dependencies
    ],
    entry_points={
        'console_scripts': [
            'c4_maker=c4_maker.c4_maker:main',  # Here, 'c4_maker.c4_maker:main' assumes that there's a main() function in your c4_maker.py
        ],
    },

    # Additional metadata about your package
    author='Your Name',
    author_email='your.email@example.com',
    description='A brief description of your project',
    license='MIT',
    keywords='example project',
    url='http://example.com/Project',  # Project home page, if any
)
