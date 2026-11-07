"""Record strace on the container's Linux filesystem, then export raw traces."""
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    staging = Path('/tmp/ptfp-paired-strace')
    staging.mkdir(exist_ok=False)
    destination = Path('/results/syscalls')
    destination.mkdir(exist_ok=True)
    status = 1
    try:
        status = subprocess.run(['strace','-ff','-ttt','-s','0','-o',str(staging/'runtime'),
            sys.executable,'-B','-u','scripts/paired_replay_worker.py',
            '--protocol','/results/protocol.json'],check=False).returncode
    finally:
        for source in staging.glob('runtime.*'):
            shutil.copyfile(source,destination/source.name)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
