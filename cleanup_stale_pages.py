"""
cleanup_stale_pages.py

Run this once from the folder where you launch `streamlit run app.py`:

    python cleanup_stale_pages.py

What it does:
  1. Prints the current working directory and this script's directory,
     so you can confirm you're actually in the right project folder
     (the traceback path "elder-ai-companion23" vs this project's real
     name is the first thing to check).
  2. Recursively searches for any files/folders that belong to the OLD
     project layout: a "pages" directory, or filenames containing
     emoji (a known Windows-unsafe pattern from an earlier version).
  3. Prints every match with its full path. Nothing is deleted
     automatically -- you confirm before anything is removed.

This does not modify app.py or views/. It only cleans up leftover
files from a previous project generation that can shadow or conflict
with this one.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def is_emoji_name(name: str) -> bool:
    return any(ord(ch) > 0x2100 for ch in name)


def find_stale_items(root: str):
    stale = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip virtualenvs / vcs / caches
        dirnames[:] = [
            d for d in dirnames
            if d not in (".git", ".venv", "venv", "__pycache__", "node_modules")
        ]
        for d in list(dirnames):
            if d.lower() == "pages":
                stale.append(("dir", os.path.join(dirpath, d)))
        for f in filenames:
            if is_emoji_name(f):
                stale.append(("file", os.path.join(dirpath, f)))
    return stale


def main():
    print(f"Current working directory : {os.getcwd()}")
    print(f"Project root (this file)  : {ROOT}")
    print()

    if os.path.basename(ROOT).lower() != os.path.basename(os.getcwd()).lower():
        print(
            "NOTE: your current working directory does not match this "
            "script's folder name. If Streamlit's traceback mentioned a "
            "different folder name than this one, you were most likely "
            "running a different, older project copy.\n"
        )

    stale = find_stale_items(ROOT)
    if not stale:
        print("No stray pages/ folders or emoji-named files found under this project.")
        return

    print(f"Found {len(stale)} stale item(s) from an older project layout:\n")
    for kind, path in stale:
        print(f"  [{kind}] {path}")

    print()
    answer = input("Delete all of the above? [y/N]: ").strip().lower()
    if answer != "y":
        print("Nothing deleted.")
        return

    import shutil
    for kind, path in stale:
        try:
            if kind == "dir":
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"Removed: {path}")
        except OSError as e:
            print(f"Could not remove {path}: {e}")


if __name__ == "__main__":
    sys.exit(main())
