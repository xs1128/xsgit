import hashlib
import os
import shutil
import json

from collections import namedtuple
from contextlib import contextmanager

GIT_DIR = None


@contextmanager
def change_git_dir(new_dir):
    """
    Change git directory
    """
    global GIT_DIR
    old_dir = GIT_DIR
    GIT_DIR = f"{new_dir}/.xsgit"
    yield
    GIT_DIR = old_dir


def init():
    """
    Create hidden dir on repo's initialization
    """
    os.makedirs(GIT_DIR)
    os.makedirs(f"{GIT_DIR}/objects")


# Abstraction for value for easier manipulation
RefValue = namedtuple("RefValue", ["symbolic", "value"])


def update_ref(ref, value, deref=True):
    """
    Set the latest commit blob as the HEAD to link history commits
    """
    ref = _get_ref_internal(ref, deref)[0]

    # Premature error check
    assert value.value
    if value.symbolic:
        value = f"ref: {value.value}"
    else:
        value = value.value

    ref_path = f"{GIT_DIR}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)

    with open(ref_path, "w") as f:
        f.write(value)


def get_ref(ref, deref=True):
    """
    A recursive function that find the ref which has the oid and value
    """
    return _get_ref_internal(ref, deref)[1]


def delete_ref(ref, deref=True):
    """
    Delete existing reference
    """
    ref = _get_ref_internal(ref, deref)[0]
    os.remove(f"{GIT_DIR}/{ref}")


def _get_ref_internal(ref, deref):
    """
    Return data in HEAD file if available
    """
    ref_path = f"{GIT_DIR}/{ref}"
    value = None

    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()

    symbolic = bool(value) and value.startswith("ref:")
    if symbolic:
        value = value.split(":", 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)

    return ref, RefValue(symbolic=symbolic, value=value)


def iter_refs(prefix="", deref=True):
    """
    Go through every ref and display according to path
    """
    refs = ["HEAD", "MERGE_HEAD"]
    for root, _, fnames in os.walk(f"{GIT_DIR}/refs/"):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(f"{root}/{name}" for name in fnames)

    for refname in refs:
        if not refname.startswith(prefix):
            continue
        ref = get_ref(refname, deref=deref)
        if ref.value:
            yield refname, ref


@contextmanager
def get_index():
    """
    Get indices and return in a dict form
    """
    index = {}
    if os.path.isfile(f"{GIT_DIR}/index"):
        with open(f"{GIT_DIR}/index") as f:
            index = json.load(f)

    yield index

    with open(f"{GIT_DIR}/index", "w") as f:
        json.dump(index, f)


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


def object_exists(oid):
    """
    Check object exists in local
    """
    return os.path.isfile(f"{GIT_DIR}/objects/{oid}")


def fetch_object_if_missing(oid, remote_git_dir):
    """
    Check if exists and then append
    """
    if object_exists(oid):
        return

    remote_git_dir += "/.xsgit"
    shutil.copy(f"{remote_git_dir}/objects/{oid}",
                f"{GIT_DIR}/objects/{oid}")


def push_object(oid, remote_git_dir):
    """
    Push object to remote
    """
    remote_git_dir += "/.xsgit"
    shutil.copy(f"{GIT_DIR}/objects/{oid}",
                f"{remote_git_dir}/objects/{oid}")
