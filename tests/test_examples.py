import subprocess
import os


def test_examples():
    python_files = os.listdir('examples/')
    for f in python_files:
        if f.endswith('.py'):
            print("Executing %s" % f)
            subprocess.check_output(['python', "examples/%s" % f])
