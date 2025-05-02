import argparse
import os
import textwrap
import sys

from . import base, data


def main():
    """
    Call and run the functions for parsing arguments
    """
    args = parse_args()
    args.func(args)


def parse_args():
    """
    Initialize parsers:
    Main: commands
        1. init
        2. hash_object
        3. cat-file
        4. write-tree
        5. read-tree
        6. commit
    """
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object")

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree")

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", nargs="?")

    return parser.parse_args()


def init(args):
    """
    Init function
    """
    data.init()
    print(
        f"Initialized empty xsgit repository in {
            os.getcwd()}/{data.GIT_DIR}"
    )


def hash_object(args):
    """
    Perform file read and pass to hash_object function in data.py
    """
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args):
    """
    Deal with stdout after getting return from decryption function
    """
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args):
    """
    Process files and directories into objects
    Dirctories will be type of "tree"
    Files will be in the type of "blob"
    """
    print(base.write_tree())


def read_tree(args):
    """
    Take in the object type and extract the encrypted data inside
    """
    base.read_tree(args.tree)


def commit(args):
    """
    Create a commit message
    """
    print(base.commit(args.message))


def log(args):
    """
    Return the log
    """

    oid = args.oid or data.get_HEAD()
    while oid:
        commit = base.get_commit(oid)

        print(f"commit {oid}\n")
        print(textwrap.indent(commit.message, "    "))
        print("")

        oid = commit.parent
