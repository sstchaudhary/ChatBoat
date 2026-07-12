import subprocess
import sys

def pip_install(packages):
    cmd = [sys.executable, '-m', 'pip', 'install'] + packages
    subprocess.check_call(cmd)

if __name__ == '__main__':
    # simple wrapper to install requirements.txt
    try:
        pip_install(['-r', 'requirements.txt'])
    except subprocess.CalledProcessError as e:
        print('pip install failed:', e)
        raise
