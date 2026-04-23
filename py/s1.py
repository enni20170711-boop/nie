import requests
from bs4 import BeautifulSoup

url = "https://nie-ctw7xk5c8-enni20170711-boops-projects.vercel.app/about"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("td")
for item in result:
	print(item.text)
	print()