import base64
import csv
from cs50 import SQL
import datetime
from decimal import Decimal
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from io import BytesIO
from matplotlib.figure import Figure
import matplotlib.patches
import pytz
import requests
from statistics import mean
import urllib
import uuid




app = Flask(__name__)

db = SQL("sqlite:///users.db")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def data(symbol, time):
    end = datetime.datetime.now(pytz.timezone("Europe/Paris"))
    if time == "ytd":
        start = datetime.datetime(end.year, 1, 1)
    else:
        start = end - datetime.timedelta(days=int(time))

    symbol = symbol.upper()
    url = (
    f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
    f"?period1={int(start.timestamp())}"
    f"&period2={int(end.timestamp())}"
    f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"Accept": "*/*", "User-Agent": request.headers.get("User-Agent")},
        )
        response.raise_for_status()

        # Returns a list of dictionaries of Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        return quotes
    except (KeyError, IndexError, requests.RequestException, ValueError):
        return None


#home page to login
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        session.clear()
        return render_template("index.html")
    email = request.form.get("name")
    password = request.form.get("password")
    account = db.execute("SELECT * FROM users WHERE email = ?;", email)
    print(account)
    if not account:
        error = "Invalid email address"
        return render_template("index.html", error=error)
    if account[0]["password"] != password:
        error = "Incorrect password"
        return render_template("index.html", error=error)
    session["user_id"] = account[0]["id"]
    return redirect("/execution")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            error = "Passwords do not match"
            return render_template("register.html", error=error)
        db.execute("INSERT INTO users (email, password) VALUES(?, ?);", email, password)
        return redirect("/")
    return render_template("register.html")

#chart page
@app.route("/charts", methods=["GET", "POST"])
@login_required
def charts():
    if request.method == "GET":
        return render_template("charts.html")
    symbol = request.form.get("ticker")
    timeframe = request.form.getlist("timeframe")
    timeframe = timeframe[0]
    inp = data(symbol, timeframe)
    if not inp:
        return render_template("charts.html", err="Invalid Ticker")


    #extract data to a list
    dates = [d['Date'] for d in inp]
    dates = [datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d-%m-%y') for date in dates]
    price = [round(Decimal(d['Close']), 2) for d in inp]
    p_last = price[len(price)-1]
    volume = [int(v['Volume']) / 1000000 for v in inp]

    #moving averages (1, 2, 3, 4, 5, 6, 7, 8, 9)
    len1 = 0
    ma1 = []
    len2 = 0
    ma2 = []
    len3 = 0
    ma3 = []
    if request.form.get("ma1") == "on":
        len1 = int(request.form.get("len1"))
    if request.form.get("ma2") == "on":
        len2 = int(request.form.get("len2"))
    if request.form.get("ma3") == "on":
        len3 = int(request.form.get("len3"))
    if len1:
        i = 1
        while i <= len(price):
            if i < len1:
                ma1.append(None)
                i += 1
            else:
                ma1.append(mean(price[i-len1:i]))
                i += 1

    if len2:
        i = 1
        while i <= len(price):
            if i < len2:
                ma2.append(None)
                i += 1
            else:
                ma2.append(mean(price[i-len2:i]))
                i += 1

    if len3:
        i = 1
        while i <= len(price):
            if i < len3:
                ma3.append(None)
                i += 1
            else:
                ma3.append(mean(price[i-len3:i]))
                i += 1

    #very complicated chart
    fig = Figure(figsize=(14, 5))
    ax = fig.subplots()
    ax.plot(dates, price, linestyle='-', color="black", label="Price")
    if ma1:
        ax.plot(dates, ma1, linestyle='-', color="blue", label="MA " + str(len1))
    if ma2:
        ax.plot(dates, ma2, linestyle='-', color="purple", label="MA " + str(len2))
    if ma3:
        ax.plot(dates, ma3, linestyle='-', color="yellow", label = "MA " + str(len3))
    ax.set_xlabel("Date")
    ax.set_ylabel("Close")
    ax.set_title(f"{symbol.upper()}")
    ax.grid(True)
    ax.set_ylim(float(min(price)) * 0.95, float(max(price)) * 1.05)
    ax.set_xticks(dates[::20 if timeframe == "1825" else 1 if timeframe == "30" else 5])
    ax.tick_params(axis='x', labelrotation=45, labelsize=6 if timeframe == "1825" else 10 )
    fig.subplots_adjust(bottom=0.17)
    fig.legend(loc="upper left")

    #volume
    if request.form.get("vol") == "on":
        col = []
        i = 0
        for val in volume:
            if i == 0:
                col.append("green")
                i += 1
            elif int(val) > int(volume[i - 1]):
                col.append("green")
                i += 1
            else:
                col.append("red")
                i += 1
        ax2 = ax.twinx()
        ax2.bar(dates, volume, color=col, alpha=0.4)
        ax2.set_ylabel("Volume (Millions)")
        ax2.ticklabel_format(axis="y", style="plain")
        ax2.set_ylim(0, float(max(volume)) * 1.5)

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    bite = base64.b64encode(buf.getbuffer()).decode("ascii")
    return render_template("charts.html", chart=bite, p_last=p_last)

@app.route("/logoff")
def logoff():
    session.clear()
    return redirect("/")

@app.route("/execution", methods=["GET", "POST"])
@login_required
def execution():
    portf = db.execute("SELECT * FROM transactions WHERE id = ?;", session["user_id"])
    fds = db.execute("SELECT funds FROM users WHERE id = ?;", session["user_id"])
    fds=round(fds[0]["funds"], 2)
    if request.method == "POST":
        dir = request.form.get("dir")
        if not dir:
            return render_template("execution.html", er="BUY / SELL NOT SELECTED", portf=portf, fds=fds)
        symbol = request.form.get("ticker")
        symbol = symbol.upper()
        quantity = int(request.form.get("qty"))
        inp = data(symbol, 1)
        if not inp:
            return render_template("execution.html", er="INVALID TICKER", portf=portf, fds=fds)
        try:
            amount = float(inp[1]["Close"]) * quantity
            prx = float(inp[1]["Close"])
        except:
            amount = float(inp[0]["Close"]) * quantity
            prx = float(inp[0]["Close"])
        # buy cases (adding on a long, unwinding a short, entering long)
        if dir == "B":
            p_prev = db.execute("SELECT * FROM transactions WHERE id = ? AND SYMBOL = ? AND QTY > 0;", session["user_id"], symbol)
            n_prev = db.execute("SELECT * FROM transactions WHERE id = ? AND SYMBOL = ? AND QTY < 0;", session["user_id"], symbol)

            if p_prev:
                db.execute("UPDATE transactions SET PRICE = ((PRICE * QTY) + (? * ?))/(QTY + ?), QTY = QTY + ?, DATE = ? WHERE id = ? AND SYMBOL = ? AND QTY > 0;", prx, quantity, quantity, quantity, datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%d-%m-%y"), session["user_id"], symbol)
            elif n_prev:
                db.execute("UPDATE transactions SET PNL = ? * (PRICE - ?), QTY = QTY + ?, DATE = ? WHERE id = ? AND SYMBOL = ? AND QTY < 0;", quantity, prx, quantity, datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%d-%m-%y"), session["user_id"], symbol)
            else:
                db.execute("INSERT INTO transactions (id, SYMBOL, QTY, PRICE, DATE) VALUES(?, ?, ?, ?, ?);", session["user_id"], symbol, quantity if dir == "B" else quantity * -1, prx, datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%d-%m-%y"))
            db.execute("UPDATE users SET funds = funds - ? WHERE id = ?;", amount, session["user_id"])

        elif dir == "S":
            p_prev = db.execute("SELECT * FROM transactions WHERE id = ? AND SYMBOL = ? AND QTY > 0;", session["user_id"], symbol)
            n_prev = db.execute("SELECT * FROM transactions WHERE id = ? AND SYMBOL = ? AND QTY < 0;", session["user_id"], symbol)

            if p_prev:
                db.execute("UPDATE transactions SET PNL = ? * (? - PRICE), QTY = QTY - ?, DATE = ? WHERE id = ? AND SYMBOL = ? AND QTY > 0;", quantity, prx, quantity, datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%d-%m-%y"), session["user_id"], symbol)
            elif n_prev:
                db.execute("UPDATE transactions SET PRICE = ((PRICE * QTY * -1) + (? * ?))/(-1 * QTY + ?), QTY = QTY - ?, DATE = ? WHERE id = ? AND SYMBOL = ? AND QTY < 0;", prx, quantity, quantity, quantity, datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%d-%m-%y"), session["user_id"], symbol)
            else:
                db.execute("INSERT INTO transactions (id, SYMBOL, QTY, PRICE, DATE) VALUES(?, ?, ?, ?, ?);", session["user_id"], symbol, quantity if dir == "B" else quantity * -1, prx, datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%d-%m-%y"))
            db.execute("UPDATE users SET funds = funds + ? WHERE id = ?;", amount, session["user_id"])
        portf = db.execute("SELECT * FROM transactions WHERE id = ?;", session["user_id"])
        fds = db.execute("SELECT funds FROM users WHERE id = ?;", session["user_id"])
        fds=round(fds[0]["funds"], 2)
        return render_template("/execution.html", portf=portf, fds=fds)
    return render_template("/execution.html", portf=portf, fds=fds)

