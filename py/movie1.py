import requests
from bs4 import BeautifulSoup

url = "http://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("filmListAllX li")
q = input("請輸入片名關鍵字")
for item in result:
	if q in item.find("img").get("alt"):
	print(item.fnd("img").get("alt")
	print("https://www.atmovies.com.tw" + item.fnd("a").get("href"))
	print("https://www.atmovies.com.tw" + item.fnd("img").get("src"))
	print()
	