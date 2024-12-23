from setuptools import setup, find_packages

setup(
    name="crypto_market_analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'pandas>=1.5.0',
        'numpy>=1.21.0',
        'matplotlib>=3.5.0',
        'seaborn>=0.11.0',
        'python-binance>=1.0.16',
        'ta-lib>=0.4.24',
        'pyyaml>=6.0.0',
        'pytest>=7.0.0',
        'python-dotenv>=0.19.0',
        'requests>=2.26.0',
        'scikit-learn>=1.0.0',
        'plotly>=5.3.0',
    ],
    python_requires='>=3.8',
) 