from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from make_top import TopMaker
from datetime import datetime
from ui import UI

app = Flask(__name__, static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class Products(db.Model):
    # 定义表名
    __tablename__ = 'products'

    # 定义字段对象
    product_id = db.Column('product_id', db.Integer, primary_key=True)
    product_code = db.Column(db.String(255))
    product_name = db.Column(db.String(255))
    website = db.Column(db.String(255))
    url = db.Column(db.String(255))


class Inventory(db.Model):
    # 定义表名
    __tablename__ = 'inventory_daily'

    # 定义字段对象
    id = db.Column('id', db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    scan_time = db.Column(db.DateTime)

    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"))


class Changes(db.Model):
    # 定义表名
    __tablename__ = 'changes'

    # 定义字段对象
    id = db.Column('id', db.Integer, primary_key=True)
    diff = db.Column(db.Integer)
    check_time = db.Column(db.DateTime)

    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"))


class Top(db.Model):
    # 定义表名
    __tablename__ = 'top'

    # 定义字段对象
    id = db.Column('id', db.Integer, primary_key=True)
    period_change = db.Column(db.Integer)
    start2end_date = db.Column(db.String)

    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"))

    info = db.relationship("Products", uselist=False, backref="own")


@app.route('/')
def index():
    try:
        html = render_template('index.html', products_num=UI.get_items_num(), inventory_crawl_times=UI.get_inventory_crawl_times(), system_time=UI.get_time_str())
        return html
    except Exception as e:
        return str(e)


@app.route('/product_list')
def p_list():
    search_field = request.args.get('search_field')
    keyword = request.args.get('keyword')

    if search_field == 'name' and keyword:
        # 产品名搜索
        pagination = Products.query.filter(Products.product_name.contains(keyword.strip())).paginate(per_page=20)
    elif search_field == 'code' and keyword:
        # 编号搜索
        pagination = Products.query.filter(Products.product_code.contains(keyword.strip())).paginate(per_page=20)
    else:
        # 默认
        pagination = Products.query.paginate(per_page=20)

    try:
        html = render_template('product_list.html', pagination=pagination)
        return html
    except Exception as e:
        return str(e)


@app.route('/product_filter')
def p_list_filter():
    """搜索器页面"""
    try:
        html = render_template('product_filter.html')
        return html
    except Exception as e:
        return str(e)


@app.route('/product_top')
def p_list_top():
    order = request.args.get('order')
    start = request.args.get('start')
    end = request.args.get('end')

    if all([start, end]):
        # 清空 top 表
        top = TopMaker()
        status = top.clear()
        if not status:
            return 'Clear TOP table failed'

        top.make_data(start, end)  # 将某段时间内的库存变化总量存入 top 表

    if order == 'asc':
        pagination = Top.query.order_by(Top.period_change.asc()).paginate(per_page=20)
    else:
        pagination = Top.query.order_by(Top.period_change.desc()).paginate(per_page=20)

    # pagination = Top.query.join(Top, Top.product_id == Products.product_id).paginate(per_page=20)

    try:
        html = render_template('product_top.html', pagination=pagination, order=order)
        return html
    except Exception as e:
        return str(e)


@app.route('/product_detail')
def p_detail():
    product_id = request.args.get('product_id')

    # 商品详情
    detail = Products.query.filter_by(product_id=product_id).one_or_none()
    if not detail:
        return 'This product is not exist'

    # 商品每日库存
    inventory = Inventory.query.filter_by(product_id=product_id).all()

    # 库存变化
    changes = Changes.query.filter_by(product_id=product_id).all()

    try:
        html = render_template('product_detail.html', detail=detail, inventory=inventory, changes=changes)
        return html
    except Exception as e:
        return str(e)


@app.template_filter('short_date')
def _trim_time(s):
    time_str_list = s.split('","')

    dates = []
    for time_str in time_str_list:
        date_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date_time.strftime('%m-%d'))

    return '","'.join(dates)


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", use_reloader=False)
    pass
