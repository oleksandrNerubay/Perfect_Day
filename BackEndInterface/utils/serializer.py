from bson import ObjectId
from datetime import datetime


def serialize(doc):
    if isinstance(doc, list):
        return [serialize(item) for item in doc]
    if isinstance(doc, dict):
        return {k: _val(v) for k, v in doc.items()}
    return doc


def _val(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _val(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_val(item) for item in v]
    return v
