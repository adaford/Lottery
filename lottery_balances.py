from selenium import webdriver
from getpass import getpass
from selenium.webdriver.chrome.options import Options
import time
import sys 
import os
from datetime import date

chrome_options = Options()
chrome_options.add_argument('log-level=3')
chrome_options.add_argument('headless')
chrome_options.add_argument("--mute-audio")

def create_driver():
	driver = webdriver.Chrome(options=chrome_options)
	driver.implicitly_wait(10)
	return driver

def open_browser(driver):
	driver.set_window_size(1920,1080)
	driver.maximize_window()
	print("loading page")
	driver.get("https://www.michiganlottery.com")

def sign_in(user,pw,driver):
	print(f"signing in {user}")
	sign_in = driver.find_element_by_id("login_button")
	while not sign_in.is_enabled():
		time.sleep(1)
	sign_in.click()
	email_input = driver.find_element_by_id('user')
	pw_input = driver.find_element_by_id('password')
	email_input.send_keys(user)
	pw_input.send_keys(pw)
	driver.find_element_by_id('submit').submit()
	print(f"signed in {user}")

def refresh(driver):
	while 1:
		try:
			menu_arrow = driver.find_element_by_id('account-status-button')
		except:
			time.sleep(.2)
			continue
		if menu_arrow:
			time.sleep(.5)
			break

	try:
		ad = driver.find_element_by_id('modalTitle')
		if ad:
			driver.refresh()
			print("ad found - page refreshed")
			time.sleep(5/len(drivers))  # wait for refresh to finish
	except:
		print("no ad found")
		pass

	try:
		asked_age = driver.find_element_by_xpath('//*[@id="yes18"]')
		asked_age.click()
	except:
		pass

def menu_click(driver):
	while 1:
		try:
			menu_arrow = driver.find_element_by_id('account-status-button')
		except:
			time.sleep(.2)
			continue
		if menu_arrow:
			break

	while not menu_arrow.is_enabled():
		time.sleep(.3)
	try:
		menu_arrow.click()
	except:
		driver.refresh()
		time.sleep(5)
		menu_arrow.click()
	time.sleep(.5)

def write_to_file(driver, username):
	#print prize won
	f = open(f"/home/ec2-user/lotto/balance.txt",'a')
	balance = driver.find_element_by_xpath('//*[@id="player-balance"]').text
	f.write(f"{username}: {balance} \n")
	f.close()

def find_balance(usernames, passwords):
	drivers = [create_driver() for _ in range(len(usernames))]

	for driver in drivers:
		open_browser(driver)

	for i in range (len(drivers)):
		sign_in(usernames[i], passwords[i], drivers[i])

	for driver in drivers:
		refresh(driver)

	for i in range (len(drivers)):
		menu_click(drivers[i])
	
	for i in range (len(drivers)):
		write_to_file(drivers[i],usernames[i])

	for d in drivers:
		d.quit()


if __name__ == '__main__':
	usernames = []
	passwords = []
	f = open("/home/ec2-user/lotto/lotto_accounts.txt","r")
	accounts_passwords = f.readlines()
	f.close()
	for a in accounts_passwords:
		a = a.split()
		usernames.append(a[0])
		passwords.append(a[1])

	for i in range(len(usernames)):
		find_balance([usernames[i]],[passwords[i]])

	f = open(f"/home/ec2-user/lotto/balance.txt",'a')
	f.write("------------NEW ---------------" + '\n')
	f.close()
