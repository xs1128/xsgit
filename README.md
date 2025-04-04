# xsgit

**xsgit** is a lightweight, educational implementation of Git written in Python, inspired by [ugit](https://github.com/mach-kernel/ugit). The purpose of this project is to build a deeper understanding of how Git works under the hood by reimplementing its core features step by step.

> ⚠️ xsgit is not a full Git replacement and is currently under development.

## 🚀 Project Goal

To learn how Git works internally — by coding it. `xsgit` focuses on simplicity and clarity, avoiding the complexity and performance optimizations of production Git. Every feature is a reflection of key Git concepts, implemented in Python and explained through readable code.

## ✅ Implemented Features

### Repository Initialization
- `xsgit init`: Initializes a new xsgit repository by setting up the `.xsgit/` directory structure.

### Object Storage
- `xsgit hash-object`: Stores file content in the object database and returns its SHA-1 hash.
- `xsgit cat-file`: Reads and prints the content of an object by its SHA-1.

### Tree Management
- `xsgit write-tree`: Writes the current directory tree into a tree object, recursively.
- `xsgit read-tree`: Loads a tree object into the working directory.

### Commit System
- `xsgit commit`: Records a commit object with a reference to the current tree and optional parent commits.
- Commit parser: Parses commit objects for inspection and reference.

## 📦 Installation (Dev Mode)

To install `xsgit` in development mode:

```bash
git clone https://github.com/yourusername/xsgit.git
cd xsgit
python3 setup.py develop --user

