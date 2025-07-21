'''
utilities
'''
import os
import random
import string
from functools import wraps
from uuid import uuid4
import bcrypt
from flask import request
from . import db

def encrypt(pw: bytes) -> bytes:
    '''
    encrypt a password
    '''
    return bcrypt.hashpw(pw, bcrypt.gensalt())

def check(pw: bytes, hash_: bytes) -> bool:
    '''
    check a password
    '''
    return bcrypt.checkpw(pw, hash_)

def random_str(l: int, charset=string.hexdigits):
    '''
    generates a random string using charset
    '''
    s = ""
    for _ in range(l):
        s += random.choice(charset)
    return s

def gentoken():
    '''
    generates a user token
    '''
    return str(uuid4())

def require_parameters(params: list[str]):
    '''
    Require parameters in JSON request or return 400
    '''
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}

            missing = [p for p in params if p not in data]
            if missing:
                return {"error": f"missing parameters: {', '.join(missing)}"}, 400

            return fn(*args, **kwargs)
        return wrapper
    return decorate

def require_bearer(fn):
    '''
    requires bearer token
    '''
    @wraps(fn)
    def decorate(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):].strip()
        else:
            print("noauth")
            return {"error": "bad/no bearer token"}, 401

        return fn(
            token=token,
            *args,
            **kwargs
        )
    return decorate

def db_transaction(fn):
    '''
    safe transaction
    '''
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with db.session() as session:
            try:
                with session.begin():
                    return fn(*args, session=session, **kwargs)
            except Exception as e:
                #print(f"[DB Error] {type(e).__name__}: {e}")
                session.rollback()
                raise e
    return wrapper

class UnauthorizedError(Exception): '''raised when an unauthorized action is preformed'''
class BadPathError(Exception): '''raised when a path is bad'''

def is_safe_path_component(s: str) -> bool:
    '''
    Reject if any path traversal parts appear anywhere
    Also reject empty strings or strings with only whitespace
    If above is OK, return True, else False
    '''
    forbidden = [".."]

    for bad in forbidden:
        if bad in s:
            return False
    if not s.strip():
        return False

    return True

def open_stored_file(s: str, mode: str):
    '''
    returns a stored file (or raises BadPathError)
    '''
    mediapath = os.path.join("static/", s)
    if not is_safe_path_component(mediapath):
        raise BadPathError(mediapath)

    return open(mediapath, mode = mode)

def tw(exc, json, code):
    '''
    tw aka trywrap
    '''
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                return result
            except exc:
                return json, code
        return wrapper
    return decorate
