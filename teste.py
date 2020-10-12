import subprocess
import os
import shutil
import time
import sys
import glob

# Extract ids from git repository
start_dir = os.getcwd()
os.chdir('./Tese')

subprocess.run(
    ['git', 'checkout', 'master', '--force'],
    capture_output=True
)

gitlog = subprocess.run(
    ['git', 'log', '--oneline'],
    capture_output=True
)

log = gitlog.stdout.decode('utf8').split('\n')
ids = [line.split(' ')[0] for line in log][:-1]

for id in ids:
	subprocess.run(['bash', '../compilar_copiar.sh', id])