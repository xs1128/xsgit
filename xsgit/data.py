import hashlib
import os
import sys

GIT_DIR = ".xsgit"


def init():
    """
    Create hidden dir on repo's initialization
    """
    os.makedirs(GIT_DIR)
    os.makedirs(f"{GIT_DIR}/objects")


def set_HEAD(oid):
    """
    Set the latest commit blob as the HEAD to link history commits
    """
    with open(f"{GIT_DIR}/HEAD", "w") as f:
        f.write(oid)


def get_HEAD():
    """
    Return data in HEAD file if available
    """
    if os.path.isfile(f"{GIT_DIR}/HEAD"):
        with open(f"{GIT_DIR}/HEAD", "r") as f:
            return f.read().strip()


def hash_object(data, type_="blob"):
    """
    Perform hashing for the data in the initialized repo
    Add a type label followed by a null byte
    """
    obj = type_.encode() + b"\x00" + data
    # Prevent any clashes of name by using sha1 encoding
    # TODO: change to stronger encryption
    oid = hashlib.sha1(obj).hexdigest()

    # Write in binary mode
    # TO-DO: Compress files into seperate directories for big-scale code
    with open(f"{GIT_DIR}/objects/{oid}", "wb") as out:
        out.write(obj)
    return oid


def get_object(oid, expected="blob"):
    """
    Read binary contents in hashed oid file
    Partition by null byte and return the contents
    """
    with open(f"{GIT_DIR}/objects/{oid}", "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got{type_}"
    return content
