"""
HMS AI/ML System for Hospital Management.
Complete AI and Machine Learning system for hospital operations.
"""

__version__ = "1.0.0"
__author__ = "HMS Developer"

from .config import *

# Lazy-load optional dependencies
try:
    from .utils.synthetic_data import *
    from .utils.preprocessing import *
    from .utils.evaluator import *
except ImportError:
    # Optional dependencies not installed - API will work without them
    pass
