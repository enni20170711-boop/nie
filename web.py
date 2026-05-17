=import requests
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


from flask import Flask, render_template, request,make_response, jsonify
from datetime import datetime
import random

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action = req["queryResult"]["action"]

    if action == "rateChoice":
        rate = req["queryResult"]["parameters"]["rate"]

        info = "這是呂恩妮的機器人，您選擇的電影分級是：" + rate

        docs = db.collection("本週新片含分級").where("rate", "==", rate).get()

        movie_titles = []

        for doc in docs:
            data = doc.to_dict()
            title = data.get("title", "")
            if title != "":
                movie_titles.append(title)

        if len(movie_titles) == 0:
            info += "\n目前查不到" + rate + "的本週上映電影。"
        else:
            info += "\n本週上映的" + rate + "電影有：\n"
            info += "\n".join(movie_titles)

    else:
        info = "抱歉，我目前還無法處理這個查詢。"

    return make_response(jsonify({"fulfillmentText": info}))

@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather")
def weather():
    # 1. 取得使用者在網頁網址或表單輸入的縣市
    # 這取代了原本的 city = input("請輸入縣市：")
    city = request.args.get("city")

    # 2. 如果使用者還沒有輸入，就先顯示一個網頁表單給他填寫
    if not city:
        return '''
            <h2>氣象查詢系統</h2>
            <form action="/weather" method="GET">
                請輸入縣市 (例如：臺中市)：<input type="text" name="city" required>
                <input type="submit" value="查詢">
            </form>
        '''

    # 3. 處理字串 (台換成臺)
    city_formatted = city.replace("台", "臺")
   
    # 4. 組合 API 網址 (已修正你原本程式碼中重複組合的問題)
    token = "rdec-key-123-45678-011121314"
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city_formatted}"
   
    # 為了避免你之前一直遇到的 10054 連線被阻擋問題，務必加上偽裝標頭
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    }

    try:
        # 發送請求，記得加上 verify=False
        Data = requests.get(url, headers=headers, verify=False, timeout=10)
       
        if Data.status_code == 200:
            json_data = json.loads(Data.text)
           
            # 依照你原本的邏輯，挖出天氣與降雨機率
            # 這裡包在 try 裡面是為了避免使用者輸入錯的縣市名稱（例如：台中縣）導致 JSON 找不到該路徑
            try:
                location_data = json_data["records"]["location"][0]
                weather_status = location_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
                rain_prob = location_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
               
                # 回傳結果加上簡單的 HTML 排版
                return f'''
                    <h2>查詢結果：{city_formatted}</h2>
                    <p>目前天氣：{weather_status}</p>
                    <p>降雨機率：{rain_prob}%</p>
                    <br><br>
                    <a href="/weather">返回重新查詢</a>
                '''
            except IndexError:
                return f"找不到「{city}」的資料，請確認縣市名稱是否輸入正確（如：臺中市）。<br><a href='/weather'>返回重新查詢</a>"
               
        else:
            return f"無法取得資料，錯誤代碼：{Data.status_code}"

    except Exception as e:
        return f"連線發生錯誤：{e}"

    return R

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)作者:呂恩妮</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
   
    # 關鍵：加上這段偽裝標頭，讓伺服器以為你是瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
   
    try:
        # 同時包含 headers 和 verify=False
        Data = requests.get(url, headers=headers, verify=False, timeout=10)
       
        if Data.status_code == 200:
            JsonData = json.loads(Data.text)
            for item in JsonData:
                R += f"{item['路口名稱']}，原因：{item['主要肇因']}: 發生 {item['總件數']}件<br>"
        else:
            R += f"無法取得資料，錯誤代碼：{Data.status_code}"
           
    except Exception as e:
        R += f"連線發生錯誤：{e}"
       
    return R

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

    # 如果沒有輸入
    if keyword == "":
        R += "<p>請輸入電影名稱關鍵字。</p>"
        R += '<br><a href="/">返回首頁</a>'
        return R

    collection_ref = db.collection("電影2B")
    docs = collection_ref.get()

    found = False

    for doc in docs:

        movie = doc.to_dict()

        title = movie.get("title", "")
        picture = movie.get("picture", "")
        hyperlink = movie.get("hyperlink", "")
        showDate = movie.get("showDate", "")

        if keyword.lower() in title.lower():

            R += f"""
            <div style="margin-bottom:30px;">

                <h2>
                    <a href="{hyperlink}" target="_blank">
                        {title}
                    </a>
                </h2>

                <p>上映日期：{showDate}</p>

                <p>
                    介紹頁：
                    <a href="{hyperlink}" target="_blank">
                        {hyperlink}
                    </a>
                </p>

                <img src="{picture}" width="200">

            </div>

            <hr>
            """

            found = True

    if not found:
        R += "<p>查無符合條件的電影。</p>"

    R += '<br><a href="/">返回首頁</a>'

    return R
    
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
