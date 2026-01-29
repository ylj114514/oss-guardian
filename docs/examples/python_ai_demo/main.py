import os
import sys
import utils


def local_taint():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        os.system(cmd)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "whoami"
    utils.execute(cmd)


if __name__ == "__main__":
    main()
