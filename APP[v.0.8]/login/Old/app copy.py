from flask import Flask, render_template, session, redirect, request, jsonify, json
from functools import wraps
from flask_mongoengine import MongoEngine
import pymongo
import datetime, time
import uuid

#print(datetime.now().date())
app = Flask(__name__)
app.secret_key = b'\xb7M\x88^S\x19\x9a\xc4n\x04\xb3\xbd\x06\xf1\xb11'

# MongoDB
client = pymongo.MongoClient('localhost', 27017)
db = client.accounts

## Live Book Update ##
app.config['MONGODB_SETTINGS'] = {
    'db': 'accounts',
    'host': 'localhost',
    'port': 27017
}
qb = db
#ufid = User().get_ufid()
qb = MongoEngine()
qb.init_app(app)

# Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')

    return wrap


#Routes
from user import routes

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard/')
@login_required

def dashboard():
    return render_template('dashboard.html')

from user.models import User 

@app.route('/dietbook/')
@login_required
def dietbook():
    return render_template('dietbook.html')

@app.route('/dietbook_automatic_load', methods = ['GET','POST'])
@login_required
def dietbook_automatic_load():
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.StringField()
        brunch = qb.StringField()
        lunch = qb.StringField()
        snack = qb.StringField()
        dinner = qb.StringField()
        details = qb.StringField()
        date = qb.DateTimeField()
    days, headings = User().retrieve_days()
    start_date = days[0]
    end_date = days[6] + datetime.timedelta(days=1)
    book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
    start_date_js = int(time.mktime(start_date.timetuple())) * 1000
    end_date_js = int(time.mktime(end_date.timetuple())) * 1000
    return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col)

@app.route('/updatebook', methods=['POST'])
def updatebook():
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.StringField()
        brunch = qb.StringField()
        lunch = qb.StringField()
        snack = qb.StringField()
        dinner = qb.StringField()
        details = qb.StringField()
        date = qb.DateTimeField()
    pk = request.form['pk']
    namepost = request.form['name']
    value = request.form['value']
    day_rs = Book.objects(id=pk).first()
    if not day_rs:
        return json.dumps({'error':'data not found'})
    else:
        if namepost == 'breakfast':
            day_rs.update(breakfast=value)
        elif namepost == 'brunch':
            day_rs.update(brunch=value)
        elif namepost == 'lunch':
            day_rs.update(lunch=value)
        elif namepost == 'snack':
            day_rs.update(snack=value)
        elif namepost == 'dinner':
            day_rs.update(dinner=value)
        elif namepost == 'details':
            day_rs.update(details=value)
    return json.dumps({'status':'OK'})    

@app.route('/add', methods=['GET', 'POST'])
def create_record():
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.StringField()
        brunch = qb.StringField()
        lunch = qb.StringField()
        snack = qb.StringField()
        dinner = qb.StringField()
        details = qb.StringField()
        date = qb.DateTimeField()
    txtbreakfast = request.form['txtbreakfast']
    txtbrunch = request.form['txtbrunch']
    txtlunch = request.form['txtlunch']
    txtsnack = request.form['txtsnack']
    txtdinner = request.form['txtdinner']
    txtdetails = request.form['txtdetails']
    daysave = Book(breakfast=txtbreakfast, brunch=txtbrunch, lunch=txtlunch, snack=txtsnack, dinner=txtdinner, details=txtdetails, date=datetime.datetime.utcnow())
    daysave.save()
    return redirect('/dietbook/')

@app.route('/delete/<string:getid>', methods = ['POST','GET'])
def delete_book(getid):
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.StringField()
        brunch = qb.StringField()
        lunch = qb.StringField()
        snack = qb.StringField()
        dinner = qb.StringField()
        details = qb.StringField()
        date = qb.DateTimeField()
    print(getid)
    days = Book.objects(id=getid).first()
    if not days:
        return jsonify({'error': 'data not found'})
    else:
        days.delete() 
        #daysempty = Book(breakfast="", brunch="", lunch="", snack="", dinner="", details="", date=days.date)
        #daysave.save()
    return redirect('/')

@app.route('/updateweek', methods=['POST','GET'])
def updateweek():
    col = str(request.form['col'])
    if col=="default":
        col = User().get_ufid()
    class Book(qb.Document):
        meta = {
            'collection': col
        }
        breakfast = qb.StringField()
        brunch = qb.StringField()
        lunch = qb.StringField()
        snack = qb.StringField()
        dinner = qb.StringField()
        details = qb.StringField()
        date = qb.DateTimeField()
    timestamp = int(request.form['timestamp'])
    dt_new = datetime.datetime.fromtimestamp(timestamp)
    days, headings = User().retrieve_days(dt_new,col)
    start_date = days[0]
    end_date = days[6] + datetime.timedelta(days=1)
    book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
    start_date_js = int(time.mktime(start_date.timetuple())) * 1000
    end_date_js = int(time.mktime(end_date.timetuple())) * 1000
    return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col)

@app.route('/dietbook_control/')
@login_required
def dietbook_control():
    class dbUser(qb.Document):
        meta = {
            'collection': "users"
        }
        name = qb.StringField()
        email = qb.StringField()
        password = qb.StringField()
        supervisors = qb.ListField()
    userlist = dbUser.objects.filter(supervisors__contains=User().get_ufid())           # Returns ALL users that include session's users email in their supervisor's list.
    return render_template('dietbook_control.html', userlist=userlist)

@app.route('/dietbook_uselect', methods=['POST','GET'])
@login_required
def dietbook_uselect():
    username = request.form.get('user')
    x = db.users.find_one({"name":username})
    col = str(x['email'])
    class Book(qb.Document):
        meta = {
            'collection': col
        }
        breakfast = qb.StringField()
        brunch = qb.StringField()
        lunch = qb.StringField()
        snack = qb.StringField()
        dinner = qb.StringField()
        details = qb.StringField()
        date = qb.DateTimeField()
    d1 = datetime.datetime.utcnow()
    ufid = col
    days, headings = User().retrieve_days(d1,ufid)
    start_date = days[0]
    end_date = days[6] + datetime.timedelta(days=1)
    book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
    start_date_js = int(time.mktime(start_date.timetuple())) * 1000
    end_date_js = int(time.mktime(end_date.timetuple())) * 1000
    return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col)

@app.route('/req_prof_form/')
@login_required
def req_prof_form():
    return render_template('req_prof_form.html')

@app.route('/addprof', methods=['POST','GET'])
@login_required
def addprof():
    prof_email = request.form.get('email')
    return User().add_supervisor(prof_email)