"""Script to automatically spin michiganlottery.com user's daily prize.
Combined with a cronjob on ec2 for fully automated prize gathering and recording.
Ugly code often times to preserve precious ec2 memory and ensure script never hits an error."""

from selenium import webdriver
from getpass import getpass
from selenium.webdriver.chrome.options import Options
import time
import sys 
import os
from datetime import datetime
from pytz import timezone
import psutil
import json
import SMS


DATE = datetime.now(timezone('US/Eastern')).strftime("%m-%d")
print(f"\n\nStarting Script at: {datetime.now(timezone('US/Eastern')).strftime('%m/%d %H:%M')}")

# no args for EC2, single index number for windows testing 
EC2_MODE = True if len(sys.argv) == 1 else False
PATH_TO_USERNAMES = "/home/ec2-user/lotto/lotto_accounts.txt" if EC2_MODE else "D:\Adam\Selenium\lottery\lotto_accounts.txt"
PATH_TO_LOGFILE = f"/home/ec2-user/lotto/logs/{DATE}.txt" if EC2_MODE else f"D:\Adam\Selenium\lottery\{DATE}.txt"
PATH_TO_BALANCES = "/home/ec2-user/lotto/balances.json" if EC2_MODE else "D:\Adam\Selenium\lottery\Balances.json"

chrome_options = Options()
chrome_options.add_argument('log-level=3')
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument('--incognito')
chrome_options.add_argument("--disable-extensions")
if EC2_MODE:
	chrome_options.add_argument('headless')


def create_driver():
	driver = webdriver.Chrome(options=chrome_options)
	if EC2_MODE:
		driver.implicitly_wait(20)
	else:
		driver.implicitly_wait(8)
	return driver


def open_browser():
	driver.set_window_size(1920,1080)
	driver.maximize_window()
	print("loading page")
	driver.get("https://www.michiganlottery.com")


def sign_in(user,pw):
	print(f"signing in {user}")
	sign_in = driver.find_element_by_id("login_button")
	count = 20
	while not sign_in.is_enabled():
		print("sign in not yet enabled")
		time.sleep(2)
		count -= 1
		if count==0:
			return False

	sign_in.click()
	email_input = driver.find_element_by_id('user')
	pw_input = driver.find_element_by_id('password')
	email_input.send_keys(user)
	pw_input.send_keys(pw)
	driver.find_element_by_id('submit').submit()
	print(f"signed in {user}")
	return True


def check_for_survey():
	driver.implicitly_wait(5)
	try:
		survey_button = driver.find_element_by_xpath('//*[@id="acsMainInvite"]/div/a[1]')
		survey_button.click()
		print("survey_button clicked")
	except:
		print("no survey_button found")
	if EC2_MODE:
		driver.implicitly_wait(20)
	else:
		driver.implicitly_wait(8)


def check_for_ads():
	try:
		ad = driver.find_element_by_id('modalTitle')
		if ad:
			driver.refresh()
			print("ad found - page refreshed")
			time.sleep(5)
	except:
		print("no ad found")


#Bypass first wave of popups
def menu_click():
	time.sleep(3)
	check_for_survey()
	check_for_ads()
	check_for_survey()

	count = 20
	menu_arrow = None
	while count:
		try:
			menu_arrow = driver.find_element_by_id('account-status-button')
			print("menu arrow found")
			time.sleep(.5)
			break

		except:
			time.sleep(1)
			print("menu arrow loading")
			count -= 1
			if not count:
				driver.save_screenshot("menu_arrow_broken.png")
				print("menu arrow broken - exiting")
				if EC2_MODE:
					driver.quit()
					exit(1)
				else:
					time.sleep(10000)

	while not menu_arrow.is_enabled():
		print("menu arrow not enabled yet")
		time.sleep(.3)
	try:
		menu_arrow.click()
	except:
		driver.save_screenshot('menu_arrow_broken.png')

	time.sleep(1.5)

	"""try:
		asked_age = driver.find_element_by_xpath('//*[@id="yes18"]')
		print("asked age 18")
		asked_age.click()
	except:
		pass"""


#Click spin button
def spin_button(username):
	spin_to_win = driver.find_element_by_id('daily-spin-to-win-button')
	spin_to_win.click()
	spin = driver.find_element_by_class_name('daily-spin-to-win-cta')
	time.sleep(1)
	try:
		spin.click()
		print(f"spinning for {username}")
	except:
		print(f"spin click broken on {username}")
	time.sleep(22)


#Save prizes won in a log file
def write_to_file(username):
	#print prize won
	f = open(PATH_TO_LOGFILE,'a')
	print("prize file opened")
	try:
		prize = driver.find_element_by_xpath('//*[@id="game-details-page"]/div[4]/div/div/p')
		print("prize found")
		print(f"{username} {prize.text}")
		f.write(f"{username} {prize.text} \n")
	except:
		print(psutil.cpu_percent())
		print(psutil.virtual_memory().percent)
		driver.save_screenshot("prize_broken.png")
		print(f"{username} prize broken")
		f.write(f"{username} prize broken\n")	
		print("prize broken, exiting")
		exit(1)		
	f.close()
	time.sleep(1)
 
 
def update_balance(index):
	balance = driver.find_element_by_xpath('//*[@id="player-balance"]').text
	data = None
	print("balance found")

	with open(PATH_TO_BALANCES, "r") as jsonFile:
		data = json.load(jsonFile)
		data[usernames[index]] = balance

	with open(PATH_TO_BALANCES, "w") as jsonFile:
		json.dump(data, jsonFile, indent=2) 

	print("balance updated")


def sign_out(index):
	print("signing out")
	driver.refresh()
	print("refreshed")
	time.sleep(5)
	drop_down = driver.find_element_by_id('account-status-button')
	print("drop_down found")
	time.sleep(5)
	count = 20
	while count:
		count -= 1
		try:
			drop_down.click()
			break
		except:
			print("drop_down.click not ready")
			time.sleep(1)
		if count==0:
			print("broken drop_down menu on sign_out, exiting")
			driver.save_screenshot("sign_out_broken.png")
			driver.quit()
			exit(1)
	print("drop_down clicked")
	time.sleep(1)

	update_balance(index)

	sign_out = driver.find_element_by_xpath('//*[@id="account-dropdown"]/div[4]/div[2]/div')
	print("sign_out found")
	time.sleep(2)
	try:
		sign_out.click()
	except:
		time.sleep(10)
		sign_out.click()
	driver.refresh()
	print("signed out")
	time.sleep(5)


#Remove accounts from usernames/passwords list that have already been spun today
def remove_accounts():
	ret = False
	if EC2_MODE:
		try:
			with open(PATH_TO_LOGFILE) as f:
				prizes = f.readlines()
				for prize in prizes:
					if len(prize) < 4:
						continue
					email_address = prize.split()[0]
					user_index = usernames.index(email_address)
					usernames.pop(user_index)
					passwords.pop(user_index)

			if len(usernames) == 0:
				print("all accounts already spun")
				ret = True
		except:
			print("No accounts to remove")

	else:
		for i in range(int(sys.argv[1])-1):
			usernames.pop(0)
			passwords.pop(0)
	return ret


#run all commands to spin wheel
def spin(index):
	logged_in = sign_in(usernames[index], passwords[index])
	if not logged_in:
		print("can't log in, exiting")
		driver.quit()
		exit(0)

	menu_click()
	spin_button(usernames[index])
	write_to_file(usernames[index])
	sign_out(index)

		
if __name__ == '__main__':
	usernames = []
	passwords = []

	#populate usernames and passwords
	with open(PATH_TO_USERNAMES,"r") as f:
		accounts_passwords = f.readlines()
	for i in range(len(accounts_passwords)):
		a = accounts_passwords[i].split()
		usernames.append(a[0])
		passwords.append(a[1])
	exit_now = remove_accounts()
	if exit_now:
		print("Script finished earlier today \n")
		exit(0)

	#run driver
	driver = create_driver()
	open_browser()
	for index in range(len(usernames)):
		spin(index)
	driver.quit()

	#text results to phone or email
	print("sending text message")
	with open(PATH_TO_BALANCES, "r") as jsonFile:
		balances = json.load(jsonFile)

	with open(PATH_TO_LOGFILE) as f:
		print("opened logfile")
		all_prizes = f.readlines()
		message = ""
		for prize in all_prizes:
			prize_array = prize.split(" ")
			prize_array.insert(1,balances[prize_array[0]])
			message += (" ").join(prize_array) + '\n'
		SMS.send(message)

	print("Script reached end \n")
