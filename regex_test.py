
import re

string = 'Date:   Sat Mar 23 22:31:51 2019 +0100'
parser = re.compile(r'(\w{3})\s+(\w{3})\s+(\d{1,2})\s+(\d\d:\d\d:\d\d)\s+(201\d)\s+')
match = parser.search(string)

print('Testing whole string:', string)
print(parser, '---', match)

parts = [
	re.compile(r'(\w{3})'),
	re.compile(r'(\d{1,2})'),
	re.compile(r'(\d\d:\d\d:\d\d)'),
	re.compile(r'(201\d)')
]

print('Testing parts')
for part in parts:
	print(part, '---', part.search(string))
