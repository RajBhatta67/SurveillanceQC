"""Transparent checks; no imputation, correction, or epidemiological inference."""
__version__ = "0.1.1rc1"
from .checks import Config, check_csv

__all__ = ["Config", "check_csv", "__version__"]
