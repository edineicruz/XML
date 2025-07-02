"""
Models module for XML Fiscal Manager Pro
Defines XML document models and their specific processing logic
"""

from .xml_models import XMLModel, NFEModel, NFCEModel, CTEModel, NFSEModel, XMLModelManager

__all__ = [
    'XMLModel',
    'NFEModel', 
    'NFCEModel',
    'CTEModel',
    'NFSEModel',
    'XMLModelManager'
] 