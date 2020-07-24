"""Script to automatically spin michiganlottery.com user's daily prize.
Combined with a cronjob on ec2 for fully automated prize gathering and recording.
Ugly code often times to preserve precious ec2 memory and ensure script never hits an error."""

from selenium import webdriver
from getpass import getpass
from selenium.webdriver.chrome.options import Options
import time
import sys 
import os
from datetime import date

EC2_MODE = True if len(sys.argv) == 1 else False
PATH_TO_USERNAMES = "/home/ec2-user/lotto/lotto_accounts.txt" if EC2_MODE else "D:\Adam\Selenium\lottery\lotto_accounts.txt"
PATH_TO_LOGFILE = f"/home/ec2-user/lotto/logs/{str(date.today())[5:]}.txt"

chrome_options = Options()
chrome_options.add_argument('log-level=3')
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument('--incognito')
if EC2_MODE:
	chrome_options.add_argument('headless')

def create_driver():
	driver = webdriver.Chrome(options=chrome_options)
	driver.implicitly_wait(20)
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
		time.sleep(1)
		count -= 1
		if count==0:
			print("saving screenshot sign_in_not_enabled")
			driver.save_screenshot("sign_in_not_enabled.png")
			if EC2_MODE:
				exit(0)
			else:
				time.sleep(10000)

	sign_in.click()
	email_input = driver.find_element_by_id('user')
	pw_input = driver.find_element_by_id('password')
	email_input.send_keys(user)
	pw_input.send_keys(pw)
	driver.find_element_by_id('submit').submit()
	print(f"signed in {user}")

#Bypass first wave of popups
def refresh():
	count = 20
	while count:
		try:
			menu_arrow = driver.find_element_by_id('account-status-button')
		except:
			time.sleep(1)
			print("menu arrow loading")
			count -= 1
			if not count:
				driver.save_screenshot("menu_arrow_broken.png")
				print("menu arrow broken - exiting")
				if EC2_MODE:
					exit(0)
				else:
					time.sleep(10000)

		if menu_arrow:
			print("menu arrow found")
			time.sleep(.5)
			break

	try:
		ad = driver.find_element_by_id('modalTitle')
		if ad:
			driver.refresh()
			print("ad found - page refreshed")
			time.sleep(5)
	except:
		print("no ad found")

	try:
		asked_age = driver.find_element_by_xpath('//*[@id="yes18"]')
		print("asked age 18")
		asked_age.click()
	except:
		pass

#Bypass second wave of popups
def menu_click():
	count = 20
	while count:
		count -= 1
		try:
			menu_arrow = driver.find_element_by_id('account-status-button')
		except:
			time.sleep(.2)
			continue
		if menu_arrow:
			print("menu arrow found 2")
			break
	if not count:
		if EC2_MODE:
			exit(0)
		else:
			time.sleep(10000)

	while not menu_arrow.is_enabled():
		print("menu arrow not enabled yet")
		time.sleep(.3)
	try:
		menu_arrow.click()
	except:
		driver.refresh()
		print("menu arrow click didn't work - refreshing")
		time.sleep(5)
		menu_arrow = driver.find_element_by_id('account-status-button')
		menu_arrow.click()
	time.sleep(.5)

#Click spin button
def spin_button(username):
	spin_to_win = driver.find_element_by_id('daily-spin-to-win-button')
	while not spin_to_win:
		print("not spin_to_win")
		time.sleep(.5)
	spin_to_win.click()
	time.sleep(1)
	spin = driver.find_element_by_class_name('daily-spin-to-win-cta')
	if spin.is_enabled():
		try:
			spin.click()
			print(f"spinning for {username}")
		except:
			print(f"spin click broken on {username}")
	time.sleep(22)

#Save prizes won in a log file
def write_to_file(username):
	#print prize won
	if EC2_MODE:
		f = open(PATH_TO_LOGFILE,'a')
		print("prize file opened")
		try:
			prize = driver.find_element_by_xpath('//*[@id="game-details-page"]/div[4]/div/div/p')
			print("prize found")
			print(f"{username} {prize.text}")
			f.write(f"{username} {prize.text} \n")
		except:
			print(f"{username} prize broken")
			f.write(f"{username} prize broken\n")			
		f.close()
	else:
		prize = driver.find_element_by_xpath('//*[@id="game-details-page"]/div[4]/div/div/p')
		print("prize found")
		print(f"{username} {prize.text}")
		f.write(f"{username} {prize.text} \n")

def sign_out():
	print("signing out")
	driver.refresh()
	print("refreshed")
	time.sleep(5)
	drop_down = driver.find_element_by_id('account-status-button')
	print("drop_down found")
	drop_down.click()
	time.sleep(.3)
	sign_out = driver.find_element_by_xpath('//*[@id="account-dropdown"]/div[4]/div[2]/div')
	print("sign_out found")
	sign_out.click()
	driver.refresh()
	print("signed out")
	time.sleep(5)

#Remove accounts from usernames/passwords list that have already been spun today
def remove_accounts():
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
		except:
			print("remove_accounts passed")
			pass
	else:
		for i in range(int(sys.argv[1])-1):
			usernames.pop(i)
			passwords.pop(i)

#run all commands to spin wheel
def spin(index):
	try:
		sign_in(usernames[index], passwords[index])
	except:
		driver.save_screenshot("sign_in.png")
	refresh()
	menu_click()
	spin_button(usernames[index])
	write_to_file(usernames[index])
	try:
		sign_out()
	except:
		driver.save_screenshot("sign_out.png")

		
if __name__ == '__main__':
	usernames = []
	passwords = []

	#populate usernames and passwords
	f = open(PATH_TO_USERNAMES,"r")
	accounts_passwords = f.readlines()
	f.close()
	for i in range(len(accounts_passwords)):
		a = accounts_passwords[i].split()
		usernames.append(a[0])
		passwords.append(a[1])
	remove_accounts()

	#run driver
	driver = create_driver()
	open_browser()
	for index in range(len(usernames)):
		spin(index)
	driver.quit()
