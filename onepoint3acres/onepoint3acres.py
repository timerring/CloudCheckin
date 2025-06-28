from twocaptcha import TwoCaptcha
import sys
import random
import json
import os
import requests
import http.cookies
import time
from .questions import questions
from telegram.notify import send_tg_notification

class OnePointThreeAcres:
	def __init__(self, cookie: str, solver: TwoCaptcha):
		self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
		self.cf_capcha_site_key = "0x4AAAAAAAA6iSaNNPWafmlz"
		# daily checkin
		self.checkin_page = "https://www.1point3acres.com/next/daily-checkin"
		self.post_checkin_url = "https://api.1point3acres.com/api/users/checkin"
		# daily question
		self.question_page = "https://www.1point3acres.com/next/daily-question"
		self.post_answer_url = "https://api.1point3acres.com/api/daily_questions"
		self.cookie = cookie
		self.solver = solver
		self.session = requests.session()
		self.session.cookies.update(http.cookies.SimpleCookie(self.cookie))
		self.header = {
			"User-Agent": self.user_agent,
			"Content-Type": "application/json",
			"Referer": "https://www.1point3acres.com/"
		}

	def daily_checkin(self):
		result = self.solver.turnstile(sitekey=self.cf_capcha_site_key, url=self.checkin_page, useragent=self.user_agent)
		# print(result)
		code = result["code"]
		# Restriction: 您的今日想说内容少于6个字母或3个中文字，请修改后再次提交！
		emoji_list = ['kx', 'ng', 'ym', 'wl', 'nu', 'ch', 'fd', 'yl', 'shuai']
		body = {
			"qdxq": random.choice(emoji_list),
			"todaysay": "没有太多想说的",
			"captcha_response": code,
			"hashkey": "",
			"version": 2
		}

		response = self.session.post(self.post_checkin_url, headers=self.header, data=json.dumps(body))
		# {
		#   "checkin-info": "签到成功",
		#   "errno": 0,
		#   "msg": "恭喜你签到成功!获得奖励 大米 1 升",
		#   "user": {
		#   # Some user info, the same as the answer_daily_question response
		#   }
		# }
		if response.status_code != 200:
			print(response.text)
			return False
		else:
			resp_json = json.loads(response.text)
			# print(resp_json["msg"])
			send_tg_notification(resp_json["msg"])
			return True

	def get_daily_task_answer(self) -> tuple[int, int]:

		print("Get daily question from 1point3acres")
		response = self.session.get(self.post_answer_url, headers=self.header)
		resp_json = json.loads(response.text)
		if resp_json["errno"] != 0 or resp_json["msg"] != "OK":
			print(response.text)
			# example response:
			# {
			# 	"errno": 0,
			# 	"msg": "OK",
			# 	"question": {
			# 		"a1": "直接告诉对方自己目前薪酬，让对方看着良心办",
			# 		"a2": "拿地里抖包袱版的工资数字要对方match",
			# 		"a3": "开一个天价，谈不拢就散伙",
			# 		"a4": "精读工资谈判宝典：https://www.1point3acres.com/bbs/thread-286214-1-1.html 知己知彼，百战不殆",
			# 		"id": 9,
			# 		"qc": "谈判工资时，哪种做法有利于得到更大的包裹？"
			# 	}
			# }
			return None, None
		# resolve the json response
		question_id = resp_json["question"]["id"]
		question = resp_json["question"]["qc"]
		question = question.strip()
		# print(f"The question of 1point3acres is: {question}")
		send_tg_notification(f"The question of 1point3acres is: {question}")
		answers = {}
		answers[1] = resp_json["question"]["a1"]
		answers[2] = resp_json["question"]["a2"]
		answers[3] = resp_json["question"]["a3"]
		answers[4] = resp_json["question"]["a4"]
		# print(f"The options of 1point3acres are: {answers}")
		send_tg_notification(f"The options of 1point3acres are: {answers}")
		answer = ""
		answer_id = 0
		if question in questions.keys():
			answer = questions[question]
			for k in answers:
				if answers[k] in answer:
					# print(f"find answer: {answers[k]} option value: {k} ")
					answer_id = k
			if answer_id == "":
				print(f"The question: {question}")
				print(f"answer not found: {answer}")
				print("欢迎提交 PR 更新问题到 question.py https://github.com/timerring/daily-actions")
				send_tg_notification(f"answer not found: {answer}, 欢迎提交 PR 更新问题到 https://github.com/timerring/daily-actions")
		else:
			print("question not found")
			send_tg_notification("question not found")
			return None, None
		return question_id, answer_id

	def answer_daily_question(self, question: int, answer: int) -> bool:
		result = self.solver.turnstile(sitekey=self.cf_capcha_site_key, url=self.question_page, useragent=self.user_agent)
		# print(result)
		code = result["code"]
		captcha_id = result["captchaId"]

		# request body example:
		# {
		# 	"qid": 9,
		# 	"answer": 4,
		# 	"captcha_response": "0sP469",
		# 	"hashkey": "",
		# 	"version": 2
		# }

		body = {
			"qid": question,
			"answer": answer,
			"captcha_response": code,
			"hashkey": "",
			"version": 2
		}

		response = self.session.post(self.post_answer_url, headers=self.header, data=json.dumps(body))
		# print(response.status_code)
		# print(response.text)
		# example response:
		# {
		#   "answer-info": "答题成功",
		#   "errno": 0,
		#   "msg": "恭喜你答题成功!获得奖励 大米 1 升",
		#   "user": {
		#     "adexpiry": 0, # ad-free subscription
		#     "adminid": 0, # administrative level or permissions
		#     "app_status": {
		#       "checkin": true,
		#       "question": true
		#     },
		#     "avatarstatus": 2,
		#     "blocked_uids": [], # your block account
		#     "credits": yourtotoalcredits(int),
		#     "emailstatus": 0,
		#     "extgroupids": "",
		#     "groupexpiry": 0,
		#     "groupid": your_user_group_id(int),
		#     "is_bind_wechat": 1,
		#     "magics": [],
		#     "majias": [], # majia
		#     "newpm": 0,
		#     "newprompt": 0,
		#     "phone_verified": 0,
		#     "regdate": your_register_date(Unixstamp, int),
		#     "uid": your_uid(int),
		#     "user_count": { # user info count
		#       "extcredits1": int,
		#       "extcredits2": int,
		#       "extcredits3": int,
		#       "extcredits4": int,
		#       "extcredits5": int,
		#       "extcredits6": int,
		#       "extcredits7": int,
		#       "extcredits8": int,
		#       "follower": int,
		#       "following": int,
		#       "posts": int,
		#       "threads": int
		#     },
		#     "username": "your_username(str)",
		#     "v_domains": [],
		#     "videophotostatus": 0
		#   }
		# }
		if "人机验证出错，请重试" in response.text:
			print("The captcha is wrong")
			send_tg_notification("The captcha is wrong")
			self.solver.report(captcha_id, False)
			return False
		else:
			self.solver.report(captcha_id, True)

		result = json.loads(response.text)
		print(result["msg"])
		send_tg_notification(result["msg"])
		if (result["errno"] == 0):
			return True
		elif (result["msg"] == "您今天已经答过题了"):
			send_tg_notification("You have already answered the question today")
			return True
		else:
			print(response.text)
			send_tg_notification(response.text)
			return False


if __name__ == "__main__":
	cookie = os.environ.get('ONEPOINT3ACRES_COOKIE').strip()
	cookie2 = os.environ.get('ONEPOINT3ACRES_COOKIE_2').strip()
	TwoCaptcha_apikey = os.environ.get('TWOCAPTCHA_APIKEY').strip()
	
	try:
		if not cookie:
			raise ValueError("Environment variable ONEPOINT3ACRES_COOKIE is not set")
		if not cookie2:
			raise ValueError("Environment variable ONEPOINT3ACRES_COOKIE_2 is not set")
		if not TwoCaptcha_apikey:
			raise ValueError("Environment variable TWOCAPTCHA_APIKEY is not set")
		
		# initialize the solver
		solver = TwoCaptcha(TwoCaptcha_apikey)
		
		# For Account 1
		# Create the instance
		acres = OnePointThreeAcres(cookie, solver)

		# daily checkin
		daily_checkin_status = acres.daily_checkin()
		if not daily_checkin_status:
			send_tg_notification("Fail to check in the 1point3acres for Account 1 (Main)")
		# daily question
		question_id, answer_id = acres.get_daily_task_answer()
		if not question_id or not answer_id:
			raise ValueError("Fail to get daily question for Account 1 (Main)")
		time.sleep(random.uniform(1, 50))
		answer_daily_question_status = acres.answer_daily_question(question_id, answer_id)
		if not answer_daily_question_status:
			raise ValueError("Fail to answer daily question for Account 1 (Main)")
		
		# For Account 2
		# Create the instance
		acres2 = OnePointThreeAcres(cookie2, solver)

		# daily checkin
		daily_checkin_status2 = acres2.daily_checkin()
		if not daily_checkin_status2:
			send_tg_notification("Fail to check in the 1point3acres for Account 2")
		# daily question
		question_id2, answer_id2 = acres2.get_daily_task_answer()
		if not question_id2 or not answer_id2:
			raise ValueError("Fail to get daily question for Account 2")
		time.sleep(random.uniform(1, 50))
		answer_daily_question_status2 = acres2.answer_daily_question(question_id2, answer_id2)
		if not answer_daily_question_status2:
			raise ValueError("Fail to answer daily question for Account 2")
		
	except Exception as err:
		print(err, flush=True)
		sys.exit(1)







