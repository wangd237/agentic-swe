"""Put the current task workspace ahead of installed packages for test subprocesses."""
import os
import sys

workspace = os.getcwd()
sys.path[:0] = [os.path.join(workspace, "src"), workspace]
