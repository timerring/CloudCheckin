from twocaptcha import TwoCaptcha
import sys
import random
import json
import os
import requests
import http.cookies
import time
from dotenv import load_dotenv
from .questions import questions
from telegram.notify import send_source_notification

load_dotenv()

# 2Captcha 验证失败时最多重试次数（含首次，默认 3 次）
MAX_CAPTCHA_RETRIES = 3

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
		self.messages = []
		self.session = requests.session()
		self.session.cookies.update(http.cookies.SimpleCookie(self.cookie))
		self.header = {
			"User-Agent": self.user_agent,
			"Content-Type": "application/json",
			"Referer": "https://www.1point3acres.com/"
		}

	def _solve_turnstile(self, page_url: str) -> dict:
		"""Solve a Cloudflare Turnstile captcha, returning the result dict."""
		return self.solver.turnstile(
			sitekey=self.cf_capcha_site_key,
			url=page_url,
			useragent=self.user_agent,
		)

	def _is_captcha_error(self, response_text: str) -> bool:
		"""Check whether a 1point3acres API response indicates a captcha failure."""
		return "人机验证出错" in response_text

	def daily_checkin(self) -> bool:
		for attempt in range(1, MAX_CAPTCHA_RETRIES + 1):
			if attempt > 1:
				sleeptime = random.uniform(3, 8)
				print(f"  [Retry] checkin attempt {attempt}/{MAX_CAPTCHA_RETRIES} (sleep {sleeptime:.1f}s)", flush=True)
				time.sleep(sleeptime)

			result = self._solve_turnstile(self.checkin_page)
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
			if response.status_code != 200:
				print(response.text, flush=True)
				continue

			resp_json = json.loads(response.text)
			if self._is_captcha_error(response.text):
				print(f"  Checkin captcha error (attempt {attempt}): {resp_json.get('msg')}", flush=True)
				continue

			self.messages.append(resp_json.get("msg", ""))
			return True

		print("Check-in failed after all retries", flush=True)
		self.messages.append("Check-in failed: captcha verification error after retries")
		return False

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
		print(f"The question of 1point3acres is: {question}")
		answers = {}
		answers[1] = resp_json["question"]["a1"]
		answers[2] = resp_json["question"]["a2"]
		answers[3] = resp_json["question"]["a3"]
		answers[4] = resp_json["question"]["a4"]
		print(f"The options of 1point3acres are: {answers}")
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
				self.messages.append(f"Answer not found: {answer}")
		else:
			print("question not found")
			self.messages.append("Daily question not found")
			return None, None
		return question_id, answer_id

	def answer_daily_question(self, question: int, answer: int) -> bool:
		for attempt in range(1, MAX_CAPTCHA_RETRIES + 1):
			if attempt > 1:
				sleeptime = random.uniform(3, 8)
				print(f"  [Retry] answer attempt {attempt}/{MAX_CAPTCHA_RETRIES} (sleep {sleeptime:.1f}s)", flush=True)
				time.sleep(sleeptime)

			result = self._solve_turnstile(self.question_page)
			code = result["code"]
			captcha_id = result["captchaId"]

			body = {
				"qid": question,
				"answer": answer,
				"captcha_response": code,
				"hashkey": "",
				"version": 2
			}

			response = self.session.post(self.post_answer_url, headers=self.header, data=json.dumps(body))

			if self._is_captcha_error(response.text):
				print(f"  Answer captcha error (attempt {attempt})", flush=True)
				self.solver.report(captcha_id, False)
				continue

			self.solver.report(captcha_id, True)

			resp_json = json.loads(response.text)
			print(resp_json.get("msg", ""), flush=True)
			self.messages.append(resp_json.get("msg", ""))
			if resp_json.get("errno") == 0:
				return True
			elif resp_json.get("msg") == "您今天已经答过题了":
				return True
			else:
				print(response.text, flush=True)
				continue

		print("Answer failed after all retries", flush=True)
		self.messages.append("Answer failed: CAPTCHA verification error after retries")
		return False


if __name__ == "__main__":
	cookie = os.environ.get('ONEPOINT3ACRES_COOKIE', '').strip()
	TwoCaptcha_apikey = os.environ.get('TWOCAPTCHA_APIKEY', '').strip()
	messages = []
	exit_code = 0
	acres = None
	
	try:
		if not cookie:
			raise ValueError("Environment variable ONEPOINT3ACRES_COOKIE is not set")
		if not TwoCaptcha_apikey:
			raise ValueError("Environment variable TWOCAPTCHA_APIKEY is not set")
		
		# initialize the solver
		solver = TwoCaptcha(TwoCaptcha_apikey)
		# Create the instance
		acres = OnePointThreeAcres(cookie, solver)

		# daily checkin
		daily_checkin_status = acres.daily_checkin()
		if not daily_checkin_status:
			raise ValueError("Fail to check in the 1point3acres")
		# daily question
		question_id, answer_id = acres.get_daily_task_answer()
		if not question_id or not answer_id:
			raise ValueError("Fail to get daily question")
		time.sleep(random.uniform(1, 50))
		answer_daily_question_status = acres.answer_daily_question(question_id, answer_id)
		if not answer_daily_question_status:
			raise ValueError("Fail to answer daily question")
		
	except Exception as err:
		print(err, flush=True)
		messages.append(f"Error: {err}")
		exit_code = 1
	finally:
		if acres:
			messages = acres.messages + messages
		send_source_notification("1POINT3ACRES", messages)

	sys.exit(exit_code)






