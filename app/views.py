import codecs
from datetime import datetime
from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import make_response
from flask import session
from io import StringIO
import pandas as pd
from app import app
from app import db
from app.models import StockHolding
from app import helpers
import time
import csv

# Global variables
offset = 10
all_records_sql = '''select a.*, b.current_price, 
    a.stock_amount * b.current_price as net_worth 
    from stock_holding a
    join current_stock_price b
    on a.stock_id = b.stock_id
    order by id desc
'''

count_each_stock_holding_sql = '''select 
a.stock_name, 
sum(a.stock_amount) as stock_amount, 
sum(a.stock_amount) * b.current_price as current_worth
from stock_holding a 
join current_stock_price b
on a.stock_id = b.stock_id
group by a.stock_name, b.current_price'''

all_current_stock_price_sql = '''select * from current_stock_price'''


@app.route('/')
def index():
    login = session.get('login')
    return render_template('index.html', login=login)


@app.route('/login', methods=['POST'])
def login():
    jsonObj = {}
    username = request.form['username']
    password = request.form['password']
    if username == 'tifa2056' and password == 'kevin2056':
        session['login'] = True
        jsonObj['msg'] = 'Login Success!'
        jsonObj['login_token'] = 1
    else:
        jsonObj['msg'] = 'Login Failed! Check again!'
        jsonObj['login_token'] = 0
    return jsonify(jsonObj)


@app.route('/records/<int:page>')
def records(page):
    if session.get('login') == None:
        return redirect('/')
    all_records = db.engine.execute(all_records_sql).fetchall()  # list
    count_each_stock_holding = db.engine.execute(count_each_stock_holding_sql).fetchall()
    net_worth_map = {}

    # count each stock holding
    print(count_each_stock_holding)

    # count net worth
    total_bought_amount = 0
    total_net_worth = 0
    total_handling_fee = 0
    for record in all_records:
        _, _, _, record_amount, close_price, handling_fee, money_spent, _, current_price, net_worth = record
        total_bought_amount += float(money_spent) + float(handling_fee)
        total_net_worth += float(net_worth)
        total_handling_fee += float(handling_fee)
    current_balance = total_net_worth - total_bought_amount
    net_worth_map['total_bought_amount'] = total_bought_amount
    net_worth_map['total_net_worth'] = total_net_worth
    net_worth_map['total_handling_fee'] = total_handling_fee
    net_worth_map['current_balance'] = current_balance
    return render_template("records.html", current=page, records=all_records,
                           net_worth_map=net_worth_map, count_each=count_each_stock_holding)


@app.route('/pick_golden_cross')
def golden_cross():
    if session.get('buy_stock') is not None and session.get('sell_stock') is not None:
        return render_template('pick_golden_cross.html', buy_stock=session.get('buy_stock'),
                               sell_stock=session.get('sell_stock'))

    buy_stock = []
    sell_stock = []

    # 大於20億股本
    share_holding_amount_greater_than_2billion = helpers.get_share_holding_amount_greater_than_2billion()

    # 黃金交叉
    golden_cross_stocks = helpers.get_golden_cross_5MA_over_20MA()

    # 死亡交叉
    dead_cross_stocks = helpers.get_dead_cross_5MA_below_20MA()

    # find stocks with trade amount greater than 1000
    for stock in golden_cross_stocks['items']:
        if stock['symid'] in str(share_holding_amount_greater_than_2billion['items']):
            ########## 週均量大於 1000 張 ##########
            soup = helpers.get_current_stock_info(stock['symid'])
            trade_amount = helpers.get_trade_amount(soup)
            if trade_amount > 1000:
                buy_stock.append(stock)

    for stock in dead_cross_stocks['items']:
        if stock['symid'] in str(share_holding_amount_greater_than_2billion['items']):
            ########## 週均量大於 1000 張 ##########
            soup = helpers.get_current_stock_info(stock['symid'])
            trade_amount = helpers.get_trade_amount(soup)
            if trade_amount > 1000:
                sell_stock.append(stock)

    print(buy_stock)
    print(sell_stock)
    print(share_holding_amount_greater_than_2billion)
    session['buy_stock'] = buy_stock
    session['sell_stock'] = sell_stock
    return render_template('pick_golden_cross.html', buy_stock=buy_stock, sell_stock=sell_stock)


@app.route("/do_posts", methods=['POST'])
def do_post():
    jsonObj = {}
    stock_id = request.form['stock_id']
    stock_info = helpers.get_current_stock_info(stock_id)
    stock_amount = float(request.form['stock_amount'])
    bought_close_price = float(request.form['bought_close_price'])
    money_spent = stock_amount * bought_close_price
    stock_name = helpers.get_stock_name(stock_info)
    buy_date = datetime.now().strftime('%Y-%m-%d')

    # json object to return to index page
    jsonObj['stock_id'] = stock_id
    jsonObj['stock_amount'] = stock_amount
    jsonObj['bought_close_price'] = bought_close_price
    jsonObj['stock_name'] = stock_name
    jsonObj['buy_date'] = buy_date
    jsonObj['handling_fee'] = 0
    jsonObj['money_spent'] = money_spent

    # insert new record
    new_record = StockHolding(stock_id=stock_id, stock_name=stock_name, stock_amount=stock_amount,
                              close_amount=bought_close_price,
                              handling_fee=0, money_spent=money_spent, buy_date=buy_date)
    db.session.add(new_record)
    db.session.commit()
    return jsonify(jsonObj)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    record = StockHolding.query.get_or_404(id)
    if request.method == 'GET':
        return render_template('edit.html', record=record)
    else:
        # update with new data
        record.stock_id = request.form['stock_id']
        record.stock_name = request.form['stock_name']
        record.stock_amount = request.form['stock_amount']
        record.close_amount = request.form['close_amount']
        record.handling_fee = request.form['handling_fee']
        money_spent = float(request.form['stock_amount']) * float(request.form['close_amount'])
        record.money_spent = money_spent
        record.buy_date = request.form['buy_date']
        db.session.commit()
        return redirect('/records/1')


@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    record = StockHolding.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect('/records/1')


@app.route('/update_stocks')
def update_current_stock_prices():
    sql_get_price = 'select * from current_stock_price'
    results = db.session.execute(sql_get_price).fetchall()
    for record in results:
        _, stock_id, _, stock_price = record
        info = helpers.get_current_stock_info(stock_id)
        price = helpers.get_current_stock_price(info)
        print(f'updating stock: {stock_id}, current price is: {price}')
        update_sql = f"UPDATE current_stock_price SET current_price = {float(price)} WHERE stock_id = '{stock_id}'"
        db.session.execute(update_sql)
        db.session.commit()
        time.sleep(2)
    return jsonify({'status': 'Done'})


@app.route('/download_csv')
def download_csv():
    all_records = db.engine.execute(all_records_sql).fetchall()  # list
    now = datetime.now().strftime('%Y-%m-%d')
    si = StringIO()
    cw = csv.writer(si)
    cw.writerows(all_records)
    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=export_records_{now}.csv".format(now=now)
    response.headers["Content-type"] = "text/csv"
    return response


@app.route('/invalidate_session')
def invalidate_session():
    session.clear()
    return jsonify({'msg': 'session_cleared'})


@app.route('/add_new_stock')
def add_new_stock_page():
    current_price = db.engine.execute(all_current_stock_price_sql).fetchall()
    return render_template('add_new_stock.html', records=current_price)


@app.route('/add_new_monitor_stock', methods=['POST'])
def add_new_monitor_stock():
    stock_id = request.form['stock_id']
    stock_name = request.form['stock_name']
    current_price = float(request.form['current_price'])
    insert_sql = "INSERT INTO current_stock_price(stock_id, stock_name, current_price) VALUES('{}', '{}', {})".format(
        stock_id, stock_name, current_price)
    db.session.execute(insert_sql)
    db.session.commit()
    time.sleep(1)
    return jsonify({'msg': 'success'})


@app.route('/delete_current_price/<int:id>', methods=['GET'])
def delete_current_price(id):
    delete_current_price_sql = "DELETE FROM current_stock_price WHERE id = '{}'".format(id)
    db.session.execute(delete_current_price_sql)
    db.session.commit()
    return redirect('/add_new_stock')


@app.route('/pick_value_stock')
def pick_value_stock_page():
    json_info = helpers.get_value_stocks_info()
    df = pd.DataFrame(json_info['data'], columns=['證券代號', '證券名稱', '殖利率(%)', '股利年度', '本益比', '股價淨值比', '財報年/季'])
    PER = pd.to_numeric(df['本益比'], errors='coerce') < 13
    EPS = pd.to_numeric(df['股價淨值比'], errors='coerce') < 0.7
    df = df[(PER & EPS)]

    get_stocks = []
    if len(df) > 50:
        for i in df.index:
            current_stock_info_soup = helpers.get_current_stock_info(df.loc[i].values[0])
            close_price = current_stock_info_soup.find_all('b')[1].get_text()
            if float(close_price) > 10:
                get_stocks.append(df.loc[i].values)
    print(get_stocks)
    return render_template('pick_value_stock.html', stocks=get_stocks)
