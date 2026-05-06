import requests
from bs4 import BeautifulSoup

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


from flask import Flask, render_template, request
from datetime import datetime
import random

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/spidermovie")
def spidermovie():
    R =""

    db = firestore.client()
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：","")

    result=sp.select(".filmListAllX li")

    total=0
    for item in result:
      movie_id = item.find("a").get("href").replace("/movie/","").replace("/","")
      title = item.find(class_="filmtitle").text
      picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
      showDate = item.find(class_="runtime").text[5:15]
      total+=1
      
      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showDate,
          "lastUpdate": lastUpdate
      }

      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

        #print(info)
    R+="網站最近更新日期："+ lastUpdate +"<br>"
    R+="總共爬取"+ str(total) + "部電影到資料庫"
    return R

@app.route("/searchMovie", methods=["GET"])
def searchMovie():
    db = firestore.client()
    # 取得使用者輸入的關鍵字
    keyword = request.args.get("keyword", "").strip()
    results = []

    # 邏輯重點：只有在有輸入關鍵字時才去資料庫抓資料，避免程式報錯
    if keyword:
        # 指向你的 Firebase 集合「電影2B」
        collection_ref = db.collection("電影2B")
        docs = collection_ref.get()
        
        for doc in docs:
            movie = doc.to_dict()
            # 比對片名是否包含關鍵字 (忽略大小寫)
            if keyword.lower() in movie.get("title", "").lower():
                # 建立一筆搜尋結果，並補上 document ID
                movie_data = {
                    "id": doc.id,
                    "title": movie.get("title"),
                    "picture": movie.get("picture"),
                    "hyperlink": movie.get("hyperlink"),
                    "showDate": movie.get("showDate")
                }
                results.append(movie_data)

    # 將結果傳送到 searchMovie.html
    return render_template("searchMovie.html", results=results, keyword=keyword)
    
@app.route("/movie1", methods=["GET"])
def movie1():
    keyword = request.args.get("keyword", "").strip()

    R = f"""
    <h1>即將上映電影查詢</h1>

    <form method="get">
        請輸入電影片名關鍵字：
        <input type="text" name="keyword" value="{keyword}">
        <input type="submit" value="查詢">
    </form>

    <hr>
    """

    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    found = False

    for item in result:
        a_tag = item.find("a")
        img_tag = item.find("img")

        if a_tag and img_tag:
            title = img_tag.get("alt")
            introduce = "https://www.atmovies.com.tw" + a_tag.get("href")
            poster = "https://www.atmovies.com.tw" + img_tag.get("src")

            if keyword == "" or keyword in title:
                R += f"""
                <div style="margin-bottom: 30px;">
                    <h2>
                        <a href="{introduce}" target="_blank">{title}</a>
                    </h2>

                    <p>
                        介紹頁：
                        <a href="{introduce}" target="_blank">{introduce}</a>
                    </p>

                    <img src="{poster}" alt="{title}" style="width: 200px;">
                </div>

                <hr>
                """
                found = True

    if not found:
        R += "<p>查無符合條件的電影。</p>"

    R += '<br><a href="/">返回首頁</a>'

    return R

@app.route("/spider1")
def spider1():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href") + "<br>" 
    return R

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    keyword = ""
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        collection_ref = db.collection("靜宜資管2026B")
        docs = collection_ref.get()

        for doc in docs:
            user = doc.to_dict()
            if keyword in user["name"]:
                results.append({
                    "name": user["name"],
                    "lab": user["lab"]
                })

    return render_template("search.html", results=results, keyword=keyword)

@app.route("/read")
def read():
    db = firestore.client()

    Temp = ""
    collection_ref = db.collection("靜宜資管2026B")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"

    return Temp


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    year  = str(now.year)   # 取得年份 
    month = str(now.month)  # 取得月份 
    day   = str(now.day)    # 取得日期 
    now = year + "年" + month + "月" + day + "日"
    return render_template("today.html", datetime = now)

@app.route("/about")
def about():
    return render_template("mis2a.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name = x, dep = y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"])
        opt = request.form["opt"]
        y = int(request.form["y"])      
        result = "您輸入的是：" + str(x) + opt + str(y)
        
        if (opt == "/" and y == 0):
            result += "，除數不能為0"
        else:
            match opt:
                case "+":
                    r = x + y
                case "-":
                    r = x - y
                case "*":
                    r = x * y
                case "/":
                    r = x / y  # 修正：之前誤寫為 x - y
                case _:
                    return "未知運算符號"
            result += "=" + str(r)  + "<br><a href=/>返回首頁</a>"          
        return result
    else:
        return render_template("math.html")

@app.route('/cup', methods=["GET"])
def cup():
    # 檢查網址是否有 ?action=toss
    #action = request.args.get('action')
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        # 0 代表陽面，1 代表陰面
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        # 判斷結果文字
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)



@app.route("/math2", methods=["GET", "POST"])
def math2():
    result = None
    if request.method == "POST":
        # 取得使用者輸入
        x = int(request.form.get("x"))
        opt = request.form.get("opt")
        y = int(request.form.get("y"))

        # 你的核心邏輯
        match opt:
            case "∧":
                result = x ** y
            case "√":
                if y != 0:
                    result = x ** (1/y)
                else:
                    result = "數學上不存在「0 次方根」"
            case _:
                result = "請輸入∧(次方)或√(根號)"
    return render_template("math2.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
