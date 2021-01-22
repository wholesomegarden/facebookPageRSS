# app.py
from flask import jsonify
import os, sys, time
import errno
import traceback

import random
import string
import json
from threading import Thread, Timer

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

# from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs

# from webwhatsapi import WhatsAPIDriver

from pprint import pprint

# from ServiceImporter import *

# # export PATH="$HOME/wholesomegarden/WhatsappReminder:$PATH"
# from ServiceLoader import *
# from MasterService import *

runLocal = False
permalinks = {}

from scraper import *

print(
'''
:::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::
::::                         ::::
::::    FACEBOOK TO JSON     ::::
::::                         ::::
:::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::
'''
)

import re
# runLocal = True
if runLocal:
	print(
	'''
	:::::::::::::::::::::::::::::::::
	::::    RUNNING LOCALLY      ::::
	:::::::::::::::::::::::::::::::::
	'''
	)
	print('export PATH="$HOME/wholesomegarden/WhatsappReminder:$PATH"')

profileDir = "/app/session/rprofile2"
# profileDir = "/app/session/"

def _count_needed_scrolls(browser, infinite_scroll, numOfPost):
	if infinite_scroll:
		lenOfPage = browser.execute_script(
			"window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
		)
	else:
		# roughly 8 post per scroll kindaOf
		lenOfPage = int(numOfPost / 8)
	print("Number Of Scrolls Needed " + str(lenOfPage))
	return lenOfPage



class PerpetualTimer:
	"""A Timer class that does not stop, unless you want it to."""

	def __init__(self, seconds, target):
		self._should_continue = False
		self.is_running = False
		self.seconds = seconds
		self.target = target
		self.thread = None

	def _handle_target(self):
		self.is_running = True
		self.target()
		self.is_running = False
		print('handled target')
		self._start_timer()

	def _start_timer(self):
		# Code could have been running when cancel was called.
		if self._should_continue:
			self.thread = Timer(self.seconds, self._handle_target)
			self.thread.start()

	def start(self):
		if not self._should_continue and not self.is_running:
			self._should_continue = True
			self._start_timer()

	def cancel(self):
		if self.thread is not None:
			# Just in case thread is running and cancel fails.
			self._should_continue = False
			self.thread.cancel()


class PageToRSS(object):
	share = None
	# groups {"service":target, "invite":groupInvite, "user":senderID, "link":self.master.newRandomID()}
	# db = {
	# 	"masters":["972512170493", "972547932000"],
	# 	"users":{"id":{"services":{"groupID":None}}},
	# 	"services":{"Reminders":{"dbID":None,"incomingTarget":None},"Proxy":{"dbID":None,"incomingTarget":None},"Danilator":{"dbID":None,"incomingTarget":None}},
	# 	"groups": {"id":"service"},
	# 	"id":"972547932000-1610379075@g.us"}
	driver = None
	page = "https://www.facebook.com/groups/supertool"

	def __init__(self):
		PageToRSS.share = self

		# self._profile = chrome_options
		#
		# chrome_options = webdriver.ChromeOptions()
		# chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
		# # chrome_options.add_argument("--headless")
		# chrome_options.add_argument("--disable-dev-shm-usage")
		# chrome_options.add_argument("--no-sandbox")
		# chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
		# chrome_options.add_argument("user-data-dir="+profileDir);
		# chrome_options.add_argument('--profile-directory='+profileDir)
		#
		# if not runLocal:
		# 	self.driver = WhatsAPIDriver(profile = profileDir, client='chrome', chrome_options=chrome_options,username="wholesomegarden")
		# else:
		# 	self.driver = WhatsAPIDriver(username="wholesomegarden",profile=None)
		# driver = self.driver
		#
		# self.driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=self._profile, **extra_params)
		self.driver = None
		self.runLocal = runLocal
		# t = PerpetualTimer(30, self.initAsync)
		# t.start()
		asyncInit = Thread(target = self.initAsync)
		asyncInit.start()

	def getDriver(
		self,
		client="firefox",
		username="API",
		proxy=None,
		command_executor=None,
		loadstyles=False,
		profile = "/app/google-chrome/Profile",
		headless=False,
		autoconnect=True,
		logger=None,
		extra_params=None,
		chrome_options=None,
		# executable_path="/app/vendor/geckodriver/"
		executable_path=None
	):
		"""Initialises the webdriver"""

		print("((((((((((((((((()))))))))))))))))")
		print("((((((((((((((((()))))))))))))))))")
		print("((((((((((((((((()))))))))))))))))")
		print("((((((((((((((((()))))))))))))))))")
		print("((((((((((((((((()))))))))))))))))")
		print("((((((((((((((((())))))))))))))))) STATTING WEBDRIVER profile - ",profile)
		# self.logger = logger or self.logger
		extra_params = extra_params or {}

		if profile is not None:
			self._profile_path = profile
			self.logger.info("Checking for profile at %s" % self._profile_path)
			if not os.path.exists(self._profile_path):
				self.logger.critical("Could not find profile at %s" % profile)
				raise WhatsAPIException("Could not find profile at %s" % profile)
		else:
			self._profile_path = None

		self.client = client.lower()
		if self.client == "firefox":
			if self._profile_path is not None:
				self._profile = webdriver.FirefoxProfile(self._profile_path)
			else:
				self._profile = webdriver.FirefoxProfile()
			if not loadstyles:
				# Disable CSS
				self._profile.set_preference("permissions.default.stylesheet", 2)
				# Disable images
				self._profile.set_preference("permissions.default.image", 2)
				# Disable Flash
				self._profile.set_preference(
					"dom.ipc.plugins.enabled.libflashplayer.so", "false"
				)
			if proxy is not None:
				self.set_proxy(proxy)

			options = Options()

			if headless:
				options.set_headless()

			options.profile = self._profile

			capabilities = DesiredCapabilities.FIREFOX.copy()
			capabilities["webStorageEnabled"] = True

			self.logger.info("Starting webdriver")
			if executable_path is not None:
				executable_path = os.path.abspath(executable_path)

				self.logger.info("Starting webdriver")
				self.driver = webdriver.Firefox(
					# firefox_binary=firefox_binary,
					capabilities=capabilities,
					options=options,
					executable_path=executable_path,
					**extra_params,
				)
			else:
				self.logger.info("Starting webdriver")
				self.driver = webdriver.Firefox(
					# firefox_binary=firefox_binary,
					capabilities=capabilities, options=options, **extra_params
				)

		elif self.client == "chrome":
			self._profile = webdriver.ChromeOptions()
			if self._profile_path is not None:
				self._profile.add_argument("user-data-dir=%s" % self._profile_path)
			if proxy is not None:
				self._profile.add_argument("--proxy-server=%s" % proxy)
			if headless:
				self._profile.add_argument("headless")
			if chrome_options is not None:
				self._profile = chrome_options
				## for option in chrome_options:
				##     self._profile.add_argument(option)
			# self.logger.info("Starting webdriver")
			self.driver = webdriver.Chrome(executable_path=executable_path,chrome_options=self._profile, **extra_params)

		elif client == "remote":
			if self._profile_path is not None:
				self._profile = webdriver.FirefoxProfile(self._profile_path)
			else:
				self._profile = webdriver.FirefoxProfile()
			capabilities = DesiredCapabilities.FIREFOX.copy()
			self.driver = webdriver.Remote(
				command_executor=command_executor,
				desired_capabilities=capabilities,
				**extra_params,
			)

		else:
			self.logger.error("Invalid client: %s" % client)
		# self.username = username
		# self.wapi_functions = WapiJsWrapper(self.driver, self)

		self.driver.set_script_timeout(500)
		self.driver.implicitly_wait(10)

		if autoconnect:
			self.connect()


	def _scroll(self, driver, infinite_scroll, lenOfPage, permalinks):
		lastCount = -1
		match = False

		while not match:
			if infinite_scroll:
				lastCount = lenOfPage
			else:
				lastCount += 1

			# driver.execute_script(
			# 	"window.scrollTo(0, 0);var lenOfPage=document.body.scrollHeight;return "
			# 	"lenOfPage;")


			more = driver.find_elements_by_xpath("//div[text()='See More']")
			for m in more:
				try:
					print("XXX")
					driver.execute_script("arguments[0].click();", m)

					# driver.executeScript((m) => { m.click();}
					# m.click()
					time.sleep(0.2)
				except:
					pass


			page = self.page
			hrefs = driver.find_elements_by_xpath("//a[@href]")
			for h in hrefs:
				find = page + "/permalink/"
				if find in h.get_attribute("href"):
					link = h.get_attribute("href").split("?")[0]
					if link not in permalinks:
						x = h.find_element_by_xpath("./../../../../../../../../../../../../../../..")
						print("~~~~~~~~~~~~~~~~")
						print(x.text)
						print("~~~~~~~~~~~~~~~~")
						if x.text is not "" and "… See More" not in x.text:
							author = x.text.split("\n")[0]
							post = x.text
							# post = "\n".join(x.text.split(" Comment")[0].split("·")[1:])
							# post = "\n".join(post.split("\n")[:-3])
							urls = self.getURLS(post)
							for url in urls:
								if "..." in url:
									urlelement = x.find_element_by_xpath("//a[text()='"+url+"']")
									# actionChains.move_to_element(urlelement)
									# urlelement.send_keys(Keys.TAB)

									# time.sleep(1)
									# urlelement = x.find_element_by_xpath("//a[text()='"+url+"']")
									print("#################")
									# for element in urlelement:
									realurl = urlelement.get_attribute("href")
									realurl = realurl.split("https://l.facebook.com/l.php?u=")[1].split("&h=")[0].replace("%3A",":").replace("%2F","/").replace("%3F","?").replace("%3D","=").split("?fbclid")[0]
									# if
									print("...................")
									print(url)
									print(realurl)
									post = post.replace(url,realurl)
							permalinks[link]={"author":author, "post":post}

			# wait for the browser to load, this time can be changed slightly ~3 seconds with no difference, but 5 seems
			# to be stable enough
			print("#########################")
			print("#########################")
			print("#########################")
			print("#########################",lastCount)
			# for a in range(lastCount):
			driver.execute_script(
				"window.scrollTo(0, Math.round(document.body.scrollHeight/5));var lenOfPage=document.body.scrollHeight;return "
				"lenOfPage;")
				# pass


			if lastCount == lenOfPage:
				match = True

			print("================================")
			print("================================")
			print("================================")
			print("================================")
			for perma in permalinks:
				print(perma)
				print(permalinks[perma])
				print("================================")
			print("LEN",len(permalinks))


	def getURLS(self,str):
		print("XXXXXX")
		res = re.findall("(?P<url>https?://[^\s]+)", str)
		print(res)
		print("XXXXXX")
		return res



	def _login(self, browser, email, password):
		browser.maximize_window()
		browser.get("http://facebook.com/login")
		browser.implicitly_wait(10)

		print(".............")
		print(browser.find_element_by_tag_name("body").text)
		print(".............")
		time.sleep(1)
		try:
			browser.find_element_by_name("email").send_keys(email)
			time.sleep(1)
			browser.find_element_by_name("pass").send_keys(password)
			time.sleep(1)
			login = browser.find_element_by_id('loginbutton')
			print(login)
			login.click()
			time.sleep(5)

			browser.implicitly_wait(10)
			print(".............")
			print(browser.find_element_by_tag_name("body").text)
			print(".............")

		except :
			traceback.print_exc()
			pass
		time.sleep(5)

	# def loop()

	def initAsync(self, data = None):
		global profileDir
		global permalinks

		''' init driver variables '''
		# if len(PageToRSS.shares) > 1:
		# 	profileDir += "-"+str(len(PageToRSS.shares))
		chrome_options = webdriver.ChromeOptions()
		if runLocal:
			executable_path = "/home/magic/wholesomegarden/facebookPageRSS/chromedriver"
			binPath = "/usr/bin/google-chrome"
			profileDir = "/home/magic/wholesomegarden/facebookPageRSS"+profileDir
		else:
			executable_path = os.environ.get("CHROMEDRIVER_PATH")
			binPath = os.environ.get("GOOGLE_CHROME_BIN")
			profileDir = "/app" + profileDir

		print(binPath, executable_path)
		print(binPath, executable_path)
		print(binPath, executable_path)
		print(binPath, executable_path)
		# input()
		chrome_options.binary_location = binPath
		# chrome_options.add_argument('incognito')
		# chrome_options.add_argument('headless')
		chrome_options.add_argument("--headless")
		chrome_options.add_argument("--disable-dev-shm-usage")
		chrome_options.add_argument("--no-sandbox")
		chrome_options.add_argument("--window-size=1420,3600")
		chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
		# user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
		# chrome_options.add_argument('user-agent={0}'.format(user_agent))
		chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US;q=0.9'})

		# chrome_options.add_argument("--user-agent=New User Agent")
		chrome_options.add_argument("user-data-dir="+profileDir);
		chrome_options.add_argument('--profile-directory='+profileDir+"rprofile2/Profile 1")


		# self.driver = WhatsAPIDriver(profile = profileDir, client='chrome', chrome_options=chrome_options,username="wholesomegarden")
		with open('facebook_credentials.txt') as file:
			EMAIL = file.readline().split('"')[1]
			PASSWORD = file.readline().split('"')[1]

		while(True):
			try:
				# permalinks = {}
				start = time.time()

				self.driver = webdriver.Chrome(executable_path,chrome_options=chrome_options)


				driver = self.driver
				# driver.get("https://facebook.com")
				self._login(driver,EMAIL,PASSWORD)
				try:
					print(driver.find_element_by_tag_name("body").text)
				except:
					print (" NO BODY ")


				driver.get(self.page)

				# print(driver.find_element_by_tag_name("body").text)
				try:
					print(driver.find_element_by_tag_name("body").text)
				except:
					print (" NO BODY ")

				# wait up to 10 seconds for the elements to become available
				driver.implicitly_wait(10)
				# Now that the page is fully scrolled, grab the source code.
				# source_data = driver.page_source

				# Throw your source into BeautifulSoup and start parsing!
				# bs_data = bs(source_data, 'html.parser')
				# print(source_data)

				time.sleep(1.5)

				numOfPost = 3 * 8
				infinite_scroll = False
				# lenOfPage = int(_count_needed_scrolls(driver, infinite_scroll, numOfPost)/3)

				self._scroll(driver, infinite_scroll, 3, permalinks)


				print("================================")
				print("================================")
				print("================================")
				print("================================")
				for perma in permalinks:
					print(perma)
					print(permalinks[perma])
					print("================================")

				# time.sleep()
				driver.close()
				print("DONE")
				print("DONE")
				print("DONE")
				print("DONE")
				print("DONE", time.time()-start, len(permalinks), list(permalinks.keys()))
			except :
				traceback.print_exc()

			time.sleep(300)




''' running master '''
master = None
timeout = time.time()
maxtimeout = 30

''' running front server '''
from flask import Flask, render_template, redirect

app = Flask(__name__,template_folder='templates')

qrfolder = os.path.join('static', 'img')
app.config['QR_FOLDER'] = qrfolder

''' setting referals '''
refs = {"yo":"https://api.WhatsApp.com/send?phone=+972512170493"}
refs["yoo"] = "https://web.WhatsApp.com/send?phone=+972512170493"

@app.route('/')
def hello_world():
	master = PageToRSS.share
	full_filename = os.path.join(app.config['QR_FOLDER'], "QR"+str(master.lastQR)+".png")
	if master.status == "LoggedIn":
		return render_template("loggedIn.html", user_image = full_filename, status = master.status)
	else:
		return render_template("index.html", user_image = full_filename, status = master.status)

@app.route('/summary')
def summary():
	global permalinks
	# d = make_summary()
	return jsonify(permalinks)

# @app.route('/<path:text>', methods=['GET', 'POST'])
# def all_routes(text):
# 	master = PageToRSS.share
#
# 	if "exit" in text:
# 		print("EXITTT")
# 		print("EXITTT")
# 		print("EXITTT")
# 		print("EXITTT")
# 		text = text.split("exit/")[1]
# 		return
# 		return redirect("https://chat.whatsapp.com/JmnYDofCd7v0cXzfBgcVDO")
# 		return render_template("exit.html", user_image = "full_filename", status = "s")
#
# 	if "join" == text:
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ")
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ")
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ")
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ")
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ")
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ")
#
# 	if "join" in text:
# 		print("JJJJJJJJJJJJJJJJJJJJJJJJJJJJJ",text,len(text))
# 		master.runningSubscriptions+=1
# 		place = master.runningSubscriptions
# 		service = "PageToRSS"
# 		if len(text.split("/")) > 1 and len(text.split("/")[1]) > 0:
# 			afterSlash = text.split("/")[1]
# 			foundService = None
# 			for serv in master.services:
# 				if afterSlash.lower() == serv.lower():
# 					foundService = serv
# 			if foundService is not None:
# 				service = foundService
#
# 		while(len(master.db["availableChats"][service]) == 0 or place < master.runningSubscriptions):
# 			time.sleep(0.5)
# 			# print("NEW USER WAITING FOR MASTER GROUP")
#
# 		firstKey = list(master.db["availableChats"][service])[0]
# 		return redirect(master.db["availableChats"][service][firstKey])
# 		#
# 		# master.backup(now = True)
# 		# runningSubscriptions-=1
# 		#
#
#
#
# 	if text.split("/")[0] in master.links:
# 		print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
# 		print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
# 		print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
# 		print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
# 		print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
# 		print("SERVING LINK "+text)
# 		linkData = master.links[text.split("/")[0]]
# 		foundCmd = False
# 		if len(text.split("/")) > 1:
# 			data = None
# 			cmd = "/".join(text.split("/")[:2])
# 			print("CCCCCCCCCCCCCCCCCCCCCC",master.links)
# 			print("CCCCCCCCCCCCCCCCCCCCCC")
# 			print("CCCCCCCCCCCCCCCCCCCCCC")
# 			print("CCCCCCCCCCCCCCCCCCCCCC")
# 			print("CCCCCCCCCCCCCCCCCCCCCC",cmd)
# 			if cmd in master.links:
# 				linkData = master.links[cmd]
# 				foundCmd = True
#
# 		if linkData is not None and "service" in linkData and "chatID" in linkData and "answer" in linkData and "invite" in linkData:
# 			# service = linkData["service"]
# 			service, chatID, answer, invite = linkData["service"], linkData["chatID"], linkData["answer"], linkData["invite"]
# 			user = chatID
# 			if "user" in linkData and linkData["user"] is not None:
# 				user = linkData["user"]
# 			if "obj" in master.services[service]:
# 				obj = master.services[service]["obj"]
# 				if obj is not None:
# 					#Get Nicknames
#
# 					toSend = ""
# 					if foundCmd:
# 						toSend += answer
# 						if len(text.split("/")) > 2:
# 							toSend += "/" + "/".join(text.split("/")[2:])
# 					else:
# 						if len(text.split("/")) > 1:
# 							toSend += "/".join(text.split("/")[1:])
#
# 					if toSend in obj.examples:
# 						print("EEEEEXXXXXXAMMMPLEEEEEE XMPL")
# 						if "answer" in obj.examples[toSend]:
# 							toSend = obj.examples[toSend]["answer"]
#
# 						master.sendMessage(chatID, toSend)
# 						time.sleep(1)
#
# 					master.ProcessServiceAsync(obj,{"origin":chatID, "user":user, "content":toSend})
#
# 				print("RRRRRRRRRRRRRRRRRRRRRedirecting")	#
# 				print("RRRRRRRRRRRRRRRRRRRRRedirecting")	#
# 				print("RRRRRRRRRRRRRRRRRRRRRedirecting")	#
# 				print("RRRRRRRRRRRRRRRRRRRRRedirecting")	#
# 				print("RRRRRRRRRRRRRRRRRRRRRedirecting")	#
# 				print("RRRRRRRRRRRRRRRRRRRRRedirecting",invite)	#
# 				return redirect(invite)
#
# 	if text in refs:
# 		return redirect(refs[text])
# 	else:
# 		return redirect("/")


def flaskRun(master):
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	print("GONNA RUN ASYNC")
	global running
	# if reminder.runners < 1 and running < 1:
	if True:
		# running += 1
		# reminder.runners += 1
		t = Thread(target=flaskRunAsync,args=[master,])
		t.start()
	else:
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
		print(runners,"!!!!!!!!!!!!!!!!!!!!!!!!!RUNNERS")
	print("AFTER GONNA RUN ASYNC")
	print("AFTER GONNA RUN ASYNC")
	print("AFTER GONNA RUN ASYNC")
	print("AFTER GONNA RUN ASYNC")


def flaskRunAsync(data):
	master = data
	# input()
	print("AAAAAAAAAAAA ASYNC")
	print("AAAAAAAAAAAA ASYNC")
	print("AAAAAAAAAAAA ASYNC")
	print("AAAAAAAAAAAA ASYNC")
	print("AAAAAAAAAAAA ASYNC")
	print("AAAAAAAAAAAA ASYNC")
	print("AAAAAAAAAAAA ASYNC")
	master = PageToRSS()
	master = PageToRSS.share
	print("9999999999999999999999999999")
	print("9999999999999999999999999999")
	print("9999999999999999999999999999")
	print("9999999999999999999999999999")



if __name__ == '__main__':
	flaskRun(master)
	print("STARTING APP")
	# print("STARTING APP")
	# print("STARTING APP")
	# print("STARTING APP")
	# print("STARTING APP")
	if runLocal :
		pass
		app.run(debug=True, host='0.0.0.0',use_reloader=False)
	# app.run(debug=True, host='0.0.0.0',use_reloader=False)
else:
	flaskRun(master)
	if runLocal :
		pass
		app.run(debug=True, host='0.0.0.0',use_reloader=False)
	# app.run(debug=True, host='0.0.0.0',use_reloader=False)
	print("STARTING APP22222222222")
	# print("STARTING APP22222222222")
	# print("STARTING APP22222222222")
	# print("STARTING APP22222222222")
	# print("STARTING APP22222222222")
	# print("STARTING APP22222222222")
