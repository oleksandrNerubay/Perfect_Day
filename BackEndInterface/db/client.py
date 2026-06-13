from pymongo import MongoClient
import config

_client = MongoClient(config.MONGO_URI)


def get_db():
    return _client[config.MONGO_DB]
