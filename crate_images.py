import os
import subprocess
import glob
import shutil

files = glob.glob('./pdfs/*pdf')

for file in files:
	hash_ = file.split('-')[1][:-4]
	subprocess.run(['pdftoppm.exe', '-png', '-r', '50', file, f"{hash_}"])
	os.makedirs(f'./images/{hash_}', exist_ok=True)
	for picture in glob.glob('*png'):
		shutil.move(picture, f'./images/{hash_}')