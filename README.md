# xsgit

**xsgit** is a lightweight Git written in Python, inspired by [ugit](https://www.leshenko.net/p/ugit/#). The main purpose of this project is to build a deeper understanding of how Git works on a low level by reimplementing its core features.

> xsgit is not a full Git replacement.

## Project Goal

To learn how Git works internally through programming. `xsgit` focuses on simplicity and clarity, not on the complexity and performance optimizations of production Git. Every feature is an important Git concepts, implemented in Python and explained through readable code and well written Docstrings.

## Implemented Features

### Repository Initialization
- `xsgit init`: Initializes a new version control directory([hidden](https://en.wikipedia.org/wiki/Hidden_file_and_hidden_directory)) by making the `.xsgit/` directory.

### Object Storage
- `xsgit hash-object`: Stores file content in the object and returns its SHA-1 hash.
- `xsgit cat-file`: Reads and outputs the content of an object by its SHA-1.

### Tree Management
- `xsgit write-tree`: Writes the current directory tree into a tree object, recursively.
- `xsgit read-tree`: Loads a tree object and store in a dict.

### Commit System
- `xsgit commit`: Records a commit object with a reference to the current tree.
- `xsgit log`: Displays the commit history starting from a given commit OID (default to show current HEAD), showing each commit's hash and message.
- `xsgit merge-base`: Finds the common ancestor of two commits.

### Branching and Navigation
- `xsgit checkout`: Switches to a different commit or branch and updates the working directory(HEAD).
- `xsgit branch`: Creates or lists branches.
- `xsgit tag`: Creates a tag pointing to a specific commit.

### Change Tracking
- `xsgit diff`: Shows the difference between commits, trees, or the working directory.
- `xsgit status`: Displays the current status of the working directory and index.
- `xsgit add`: Adds file contents to the staging area.

### Merging & Collaboration
- `xsgit merge`: Merges one branch into another and creates a new merge commit, also detects for possible fast-forward.
- `xsgit fetch`: Downloads objects and refs from a remote repository, but not the contents.
- `xsgit push`: Uploads local commits and refs to a remote repository, but not the contents.

### Other Utilities
- `xsgit show`: Displays information about a given object.
- `xsgit k`: Use GraphViz for a graphical representation of the commit [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph).


## Installation (Tested for zsh)

To install `xsgit`:

```zsh
git clone https://github.com/xs1128/xsgit.git
cd xsgit
python3 setup.py develop --user
```
## Later on
Create any folder, change into that folder(directory) and use `xsgit init` to start using xsgit.
