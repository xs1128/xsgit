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


def update_ref(ref, oid):
    """
    Set the latest commit blob as the HEAD to link history commits
    """
    ref_path = f"{GIT_DIR}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)

    with open(ref_path, "w") as f:
        f.write(oid)


def get_ref(ref):
    """
    Return data in HEAD file if available
    """
    ref_path = f"{GIT_DIR}/{ref}"

    if os.path.isfile(ref_path):
        with open(ref_path, "r") as f:
            return f.read().strip()


def iter_refs():
    """
    Go through every ref and display according to path
    """
    refs = ["HEAD"]
    for root, _, fnames in os.walk(f"{GIT_DIR}/refs/"):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(f"{root}/{name}" for name in fnames)

    for refname in refs:
        yield refname, get_ref(refname)


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
