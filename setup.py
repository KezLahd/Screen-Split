from setuptools import setup, find_packages

setup(
    name="screen_split_app",
    version="1.0.0",
    packages=find_packages(),
    package_data={
        'screen_split_app': ['*.pyw'],  # Include .pyw files
    },
    install_requires=[
        'PyQt6>=6.4.0',
        'opencv-python>=4.7.0',
        'numpy>=1.24.0',
        'mss>=9.0.1',
        'pywin32>=305',
    ],
    entry_points={
        'console_scripts': [
            'screen-split=screen_split_app.main:main',
        ],
    },
    author="KezLahd",
    author_email="kezzajacko787@gmail.com",
    description="A screen splitting application with camera and logo support",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/KezLahd/Screen-Split",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
)