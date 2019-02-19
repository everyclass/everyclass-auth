from flask import current_app as app
from pymongo import MongoClient


def init_pool(current_app):
    """创建连接池，保存在 app 的 mysql_pool 对象中"""
    current_app.mongo = MongoClient(**current_app.config['MONGO'])


def get_connection():
    """在连接池中获得连接"""
    return app.mongo[app.config['MONGO_DB']]