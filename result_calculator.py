import os
from collections import Counter
from datetime import date
def main():
	all_prizes = Counter()
	total_prizes_counted = 0

	path = 'logs'
	for filename in os.listdir(path):
		if os.path.isdir(f"{path}/{filename}"):
			continue
		with open(f"{path}/{filename}",'r') as f:
			lines = f.readlines()
			for line in lines:
				if line[0:7] == 'No spin' or line[0:5] == "Can't":
					continue
				line = line.rstrip().strip('!.')
				prize = " ".join(line.split(" ")[3:])
				if prize == '':
					continue
				all_prizes[prize] += 1
				total_prizes_counted += 1

	with open('calculated.txt','a') as f:
		f.write(f"--------------{str(date.today())[5:].replace('-','/')}/{str(date.today())[0:5]}--------------\n")
		f.write(f"Total prizes counted: {total_prizes_counted} \n")
		for prize in all_prizes.most_common():
			f.write(f"{prize[0].lstrip('a ')}: {str(100*prize[1]/total_prizes_counted)[0:5]}% \n")
		f.write("------------------end------------------\n\n")

main()
