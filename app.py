from flask import Flask, flash, render_template, request, abort, views, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Markup
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie
from flask_script import Manager as Managers
from flask_script import Server as Servers
from flask_bootstrap import Bootstrap
from utils.create_name import random_name
from utils.create_number import create_phone
import random
import datetime

app = Flask(__name__)
app.secret_key = "123"
HOSTNAME = '127.0.0.1'
PORT = '3306'
FIRST = True
DATABASE = 'naturalgas'
USERNAME = 'root'
PASSWORD = 'root'
DB_URI = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(username=USERNAME,
                                                                                        password=PASSWORD,
                                                                                        host=HOSTNAME, port=PORT,
                                                                                        db=DATABASE)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

db = SQLAlchemy(app)

managers = Managers(app)
Bootstrap(app)
managers.add_command("runserver", Servers(
    host='0.0.0.0'))


# area
class Area(db.Model):
    __tablename__ = "area"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    gasprice = db.Column(db.Float)
    is_used = db.Column(db.CHAR(255))


# log
class Log(db.Model):
    __tablename__ = "log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.VARCHAR(255))
    kind = db.Column(db.CHAR(2), comment="日志内容所属范围（1-user,2-account,3-area,4-整体扣费)")
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)


# 图表 直方图
def bar_base(title, x_data, y_name, y_data) -> Bar:
    c = (
        Bar()
            .add_xaxis(x_data)
            .add_yaxis(y_name, y_data)
            .set_global_opts(title_opts=opts.TitleOpts(title=title))
    )
    return c


# 图表  饼图
def pie_base(title, y_data) -> Pie:
    c = (
        Pie()
            .add(title, y_data)
    )
    return c


# Manager
class Management(db.Model):
    __tablename__ = "manager"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.VARCHAR(30))
    password = db.Column(db.VARCHAR(30))
    type = db.Column(db.Integer)
    area_id = db.Column(db.Integer)


# User
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.VARCHAR(255))
    telephone = db.Column(db.VARCHAR(12))
    area_id = db.Column(db.Integer)


# Dosage
class Dosage(db.Model):
    __tablename__ = "dosage"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    used = db.Column(db.Float)
    paid = db.Column(db.Float)


# Accout
class Accout(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    balance = db.Column(db.Float)


# 插入
def insert(u):
    flag = False
    try:
        db.session.add(u)  # 添加数据对象
        db.session.commit()  # 事务提交
        flag = True
    except:
        db.session.rollback()  # 事务回滚
    return flag


# 删除
def delete(u):
    flag = False
    try:
        db.session.delete(u)
        db.session.commit()  # 事务提交
        flag = True
    except:
        db.session.rollback()  # 事务回滚
    return flag


# 生成Log
def create_log(content, kind):
    log = Log(content=content, kind=kind)
    flag = False
    try:
        db.session.add(log)  # 添加数据对象
        db.session.commit()  # 事务提交
        flag = True
    except:
        db.session.rollback()  # 事务回滚
    return flag


# 登录验证
def check_manager(name, password):
    manager = Management.query.filter_by(username=name).first()
    if not manager:
        return False
    else:
        psw = manager.password
        if password == psw:
            session.permanent = True
            if manager.type == 1:
                session['type'] = True
            return manager.area_id
        else:
            return -255


# 在线充值
def check_user(name, money):
    user = User.query.filter_by(name=name).first()
    user_id = user.id
    account = Accout.query.filter_by(user_id=user_id).first()
    account.update({'balance': account.balance + money})


# 生成dosage
@app.route('/dosage/create')
def create_dosage():
    users = User.query.filter_by().all()
    for user in users:
        user_id = user.id
        paid = random.random() * 999
        used = paid + random.random() * 99
        dosage = Dosage(user_id=user_id, used=used, paid=paid)
        insert(dosage)
    content = "新导入{}位用户的dosage信息".format(len(users))
    create_log(content, 4)
    return "success"


@app.route('/')
def hello_world():
    flash("")
    # db.create_all()
    return render_template('index.html')


@app.before_request
def before_user():
    if request.path in ['/userlogin', '/users/login']:
        pass
    else:
        if request.path in ['/', '']:
            if 'user' in session and 'type' in session:
                return redirect('/menu')
        if request.path not in ['/', '', '/manager/login', '/manager/logout']:
            if 'user' in session and 'type' in session:
                pass
            else:
                return render_template('index.html', backCode=1)


# 在线生成数据
@app.route('/user/create/')
def create():
    random_users = []
    for i in range(100):
        random_area_id = [random.randint(1, 34)]
        name = random_name()
        tele = create_phone()
        user = User(name=name, telephone=tele, area_id=random_area_id)
        random_users.append(user)
    db.session.add_all(random_users)
    db.session.commit()
    content = "新导入{}位用户e信息".format(len(random_users))
    create_log(content, 1)
    return "create success!"


@app.route('/user/delete', methods=['GET', 'POST'])
def delete_user():
    if "type " not in session:
        abort(403)
    else:
        if session['type'] == 0:
            abort(403)
    id = request.args.get("id")
    delete(User.query.filter_by(id=id).first())
    delete(Accout.query.filter_by(user_id=id).first())
    delete(Dosage.query.filter_by(user_id=id).first())
    content = "删除了id为{}的用户".format(id)
    create_log(content, 1)
    users = User.query.filter_by().all()
    return render_template('user_menu.html', users=users, Delete=1)


@app.route('/userlogin')
def login_user():
    return render_template('userlogin.html')


@app.route('/users/login', methods=['GET', 'POST'])
def login_user_judge():
    form = request.form
    n = form.get('username')
    print(n)
    session['user'] = True
    session['type'] = 1
    user = User.query.filter_by(telephone=n).first()
    try:
        # user_id = us.id
        # user = User.query.filter_by(id=user_id).first()
        balance = Accout.query.filter_by(user_id=user.id).first().balance
        area = Area.query.filter_by(id=user.area_id).first()
        area_name = area.name
        return render_template('user_own.html', name=user.name, id=user.id, telephone=user.telephone, area=area_name,
                               area_id=user.area_id, balance=balance)
    except Exception as e:
        print(e)
        return render_template('userlogin.html')


@app.route('/user/update', methods=['POST'])
def update_user():
    form = request.form
    id = form.get('id')
    name = form.get('name')
    telephone = form.get('telephone')
    area_name = form.get('area')
    user = User.query.filter_by(id=id).first()
    if user.name != name and name:
        user.name = name
    if user.telephone != telephone and telephone:
        user.telephone = telephone
    area = Area.query.filter_by(id=user.area_id).first()
    if area.name != area_name and area_name:
        area_id = Area.query.filter_by(name=area_name).first().id
        if area_id:
            user.area_id = area_id
    try:
        db.session.commit()
    except:
        pass
    user = User.query.filter_by(id=id).first()
    area_name = Area.query.filter_by(id=user.area_id).first().name
    balance = Accout.query.filter_by(user_id=user.id).first().balance
    content = "更新了 id = {} 用户的信息".format(id)
    create_log(content, 1)
    return render_template('user.html', name=user.name, id=user.id, telephone=user.telephone, area=area_name,
                           area_id=user.area_id, balance=balance, message=True)
    # users = User.query.filter_by().all()
    # return render_template('user_menu.html', users=users)


@app.route('/user/information', methods=['GET', 'POST'])
def get_user_information():
    id = request.args.get("id")
    user = User.query.filter_by(id=id).first()
    balance = Accout.query.filter_by(user_id=id).first().balance
    area = Area.query.filter_by(id=user.area_id).first()
    area_name = area.name
    content = "请求的id = {}的用户信息".format(id)
    create_log(content, 5)
    return render_template('user.html', name=user.name, id=user.id, telephone=user.telephone, area=area_name,
                           area_id=user.area_id, balance=balance)


@app.route('/user/getNumber', methods=['GET', 'POST'])
def getNumberByUsername():
    name = request.args.get('name')
    user = User.query.filter_by(name=name).first()
    if user:
        return user.telephone
    else:
        return ""


# 在线生成account
@app.route('/account/create')
def create_account():
    random_account = []
    users = User.query.filter_by().all()
    for user in users:
        user_id = user.id
        account = Accout(user_id=user_id, balance=100.0)
        random_account.append(account)
    db.session.add_all(random_account)
    db.session.commit()
    return "create success!"


@app.route('/account/add', methods=['GET', 'POST'])
def add_account():
    form = request.form
    id = form.get('id')
    money = form.get('money')
    try:
        user = User.query.filter_by(id=id).first()
        user_id = user.id
        account = Accout.query.filter_by(user_id=user_id).first()
        account.balance = account.balance + float(money)
        db.session.commit()
        content = "为 id = {}的用户充值了{}".format(id, money)
        create_log(content, 2)
    except:
        print("[后台]:something is wrong...")
        pass
    user = User.query.filter_by(id=id).first()
    balance = Accout.query.filter_by(user_id=id).first().balance
    area = Area.query.filter_by(id=user.area_id).first()
    area_name = area.name
    return render_template('user.html', name=user.name, id=user.id, telephone=user.telephone, area=area_name,
                           area_id=user.area_id, balance=balance, message=True)


@app.route('/area/all')
def area_all():
    areas = Area.query.filter_by().all()
    return render_template('area_all.html', areas=areas)


@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if 'user' not in session:
        abort(403)
    else:
        if session.get('area_id') == -1:
            return render_template('menu.html', part=1)
        else:
            return render_template('menu.html', part=0)


@app.route('/menu/echart/area')
def menu_echart_area():
    areas = Area.query.filter_by().all()
    x_data = [area.name for area in areas]
    y_data = [area.gasprice for area in areas]
    c = bar_base('全国各地区气费表', x_data, '气费', y_data)
    return Markup(c.render_embed())


@app.route('/menu/echart/arrears')
def menu_echart_arrears():
    arrears_users = []
    if session.get('area_id') != -1:
        area_name = Area.query.filter_by(id=session.get('area_id')).first().name
        users = User.query.filter_by(area_id=session.get('area_id')).all()
    else:
        area_name = "全国"
        users = User.query.filter_by().all()
    for user in users:
        gas_price = Area.query.filter_by(id=user.area_id).first().gasprice
        dosage = Dosage.query.filter_by(user_id=user.id).first()
        unpaid = dosage.used - dosage.paid
        balance = Accout.query.filter_by(user_id=user.id).first().balance
        print(gas_price * unpaid)
        if balance < gas_price * unpaid:
            arrears_users.append((user, round(gas_price * unpaid - balance, 3)))
    data = []
    data.append(('欠费的', len(arrears_users)))
    data.append(('未欠费的', len(users) - len(arrears_users)))
    c = pie_base("{} 欠费占比".format(area_name), data)
    return Markup(c.render_embed())


@app.route('/menu/ChangeDosage')
def menu_change_dosage():
    arrears_users = []
    if session.get('area_id') != -1:
        users = User.query.filter_by(area_id=session.get('area_id')).all()
    else:
        users = User.query.filter_by().all()
    for user in users:
        gas_price = Area.query.filter_by(id=user.area_id).first().gasprice
        dosage = Dosage.query.filter_by(user_id=user.id).first()
        unpaid = dosage.used - dosage.paid
        account = Accout.query.filter_by(user_id=user.id).first()
        balance = account.balance
        print(gas_price * unpaid)
        if balance < gas_price * unpaid:  # 欠费
            dosage.paid += balance / gas_price
            account.balance = 0
            db.session.commit()
        else:
            dosage.paid += unpaid
            account.balance = account.balance - unpaid * gas_price
            db.session.commit()
    content = "刷新了账单..."
    create_log(content, 4)
    return render_template('menu.html')


@app.route('/menu/add/dosage')
def add_menu_dosage():
    usernames = []
    if session.get('area_id') != -1:
        users = User.query.filter_by(area_id=session.get('area_id')).all()
    else:
        users = User.query.filter_by().all()
    for user in users:
        usernames.append(user.name)
    return render_template('menu_add_dosage.html', usernames=usernames)


@app.route('/menu/add/dosage/form', methods=['GET', 'POST'])
def add_menu_dosage_form():
    form = request.form
    name = form.get('name')
    gas_used = form.get('gas_used')
    user = User.query.filter_by(name=name).first()
    dosage = Dosage.query.filter_by(user_id=user.id).first()
    try:
        dosage.used = dosage.used + float(gas_used)
        db.session.commit()
    except:
        pass
    content = "添加了用户 id = {}的账单情况，使用气费新增量为 {}".format(user.id, gas_used)
    create_log(content, 4)
    return render_template('menu.html', backCode=200)


@app.route('/menu/manager')
def menu_manager():
    results = []
    managers = Management.query.filter(Management.area_id != -1).all()
    areas = Area.query.filter_by().all()
    for m in managers:
        results.append((m.id, m.username, Area.query.filter_by(id=m.area_id).first().name, m.type))
    return render_template('menu_managers.html', managers=results, areas=areas)


@app.route('/menu/manager/add', methods=['GET', 'POST'])
def add_manager():
    results = []
    form = request.form
    name = form.get('name')
    password = form.get('password')
    area = form.get('area')
    area_id = Area.query.filter_by(name=area).first().id
    manager = Management(username=name, password=password, area_id=area_id, type=1)
    insert(manager)
    managers = Management.query.filter(Management.area_id != -1).all()
    for m in managers:
        results.append((m.id, m.username, Area.query.filter_by(id=m.area_id).first().name, m.type))
    areas = Area.query.filter_by().all()
    content = "添加了地区 {} 的管理员".format(area)
    create_log(content, 5)
    return render_template('menu_managers.html', managers=results, areas=areas)


@app.route('/menu/manager/cancel')
def menu_manger_cancel():
    id = request.args.get('id')
    type = int(request.args.get('type'))
    print("id={}".format(id))
    m = Management.query.filter_by(id=id).first()
    if type == 1:
        m.type = 0
        db.session.commit()
    else:
        m.type = 1
        db.session.commit()
    results = []
    managers = Management.query.filter(Management.area_id != -1).all()
    for m in managers:
        results.append((m.id, m.username, Area.query.filter_by(id=m.area_id).first().name, m.type))
    return render_template('menu_managers.html', managers=results)


@app.route('/area/change', methods=['POST'])
def change_area():
    form = request.form
    area_id = form.get('id')
    gasprice = form.get('gasprice')
    if session.get('area_id') == -1 or area_id == session.get('area_id'):
        area = Area.query.filter_by(id=area_id).first()
        area.gasprice = gasprice
        db.session.commit()
        content = "调整了{}地区的天然气费到{}".format(area.name, gasprice)
        create_log(content, 3)
        return render_template('area.html', area=area)
    else:
        abort(403)


@app.route('/area/one', methods=['GET'])
def area_one():
    area_id = request.args.get('area_id')
    area = Area.query.filter_by(id=area_id).first()
    return render_template('area.html', area=area)


@app.route('/area/stop', methods=['GET'])
def stop_area():
    page = request.args.get('page')
    is_used = request.args.get('is_used')
    try:
        area_id = int(request.args.get('area_id'))
    except:
        area_id = -1
    if session.get('area_id') == -1 or area_id == session.get('area_id'):
        area = Area.query.filter_by(id=area_id).first()
        areas = Area.query.filter_by().all()
        area.is_used = is_used
        db.session.commit()
        content = "改变了{}地区的使用状态为{}".format(area.name, is_used)
        create_log(content, 3)
        if page == "all":
            return render_template('area_all.html', areas=areas)
        elif page == "one":
            return render_template('area.html', area=area)
        else:
            abort(403)
    else:
        abort(403)


@app.route('/search/all')
def search_all():
    return render_template('search.html')


@app.route('/search/area', methods=['POST'])
def search_area():
    form = request.form
    search_name = form.get('search')
    area = Area.query.filter(Area.name.like("%" + search_name + "%") if search_name is not None else "").first()
    if area:
        return render_template('area.html', area=area)
    else:
        areas = Area.query.filter_by().all()
        return render_template('area_all.html', backCode=404, areas=areas)


@app.route('/search/result')
def search_result():
    keyword = request.args.get('KeyWord')
    print(keyword)
    results = []
    if keyword in 'arrears':
        arrears_users = []
        users = User.query.filter_by().all()
        for user in users:
            gas_price = Area.query.filter_by(id=user.area_id).first().gasprice
            dosage = Dosage.query.filter_by(user_id=user.id).first()
            unpaid = dosage.used - dosage.paid
            balance = Accout.query.filter_by(user_id=user.id).first().balance
            print(gas_price * unpaid)
            if balance < gas_price * unpaid:
                arrears_users.append((user, round(gas_price * unpaid - balance, 3)))
        print(len(arrears_users))
        return render_template('user_arrears.html', users=arrears_users, backCode=len(arrears_users))
    elif "user" in keyword:
        try:
            name = keyword.split()[-1]
        except:
            name = ""
        results = User.query.filter(User.name.like("%" + name + "%") if name is not None else "").all()
        if len(results) > 0:
            return render_template('user_menu.html', users=results)
        else:
            if name == '*':
                results = User.query.filter_by().all()
                return render_template('user_menu.html', users=results)
            else:
                return render_template('search.html')
    else:
        return render_template('search.html')


@app.route('/manager/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if request.args.get('key') == session['username']:
            users = User.query.filter_by().all()
            return render_template('user_menu.html', users=users)
        else:
            return render_template('index.html')
    form = request.form
    username = form.get('username')
    password = form.get('password')
    if not username:
        flash("please input your username...")
        return render_template('index.html')
    if not password:
        flash("please input your password...")
        return render_template('index.html')
    if check_manager(username, password) != -255:
        flash("")
        session['user'] = True
        session['area_id'] = check_manager(username, password)
        if session.get('area_id') == -1:
            users = User.query.filter_by().all()
        else:
            users = User.query.filter_by(area_id=session.get('area_id')).all()
        content = "管理员登录系统..."
        create_log(content, 5)
        return render_template('user_menu.html', users=users)
    else:
        flash("username or password is wrong...")
        content = "管理员登录失败..."
        create_log(content, 6)
        return render_template('index.html')


@app.route('/manager/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('index.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('not_found.html')


@app.errorhandler(403)
def ban_invite(e):
    return render_template('index.html', backCode=403)


if __name__ == '__main__':
    managers.run(host='0.0.0.0', port=5000, debug=False)
    # managers.run('127.0.0.1')
