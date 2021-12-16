from flask import (Flask, render_template, url_for, redirect, request, flash, session)
from flask_cors import CORS
from model import setup_db, User, Account
from datetime import datetime
import bcrypt
import random
import uuid

app = Flask(__name__)
setup_db(app)
CORS(app)
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +'abcdefghijklmnopqrstuvxyz' +'0123456789')) for i in range(20) ])


@app.route('/')
def index():
    if 'id' in session:
        id = session['id']
        return redirect(url_for('user', userId=id) )
    
    else:
        return redirect(url_for('login'))        


@app.route('/signup/', methods=["GET", "POST"])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    else:
        username = request.form.get('username')
        passwd1 = request.form.get('password1')
        passwd2 = request.form.get('password2')
        user = User.query.filter_by(username=username).all()
        if passwd1 != passwd2:
            flash('passwords do not match')
            return redirect(url_for('signup'))
        
        if len(user) != 0:
            flash('That username is taken')
            return redirect(url_for('signup'))

        hashed = bcrypt.hashpw(passwd1.encode('utf-8'),bcrypt.gensalt())
        stored = hashed.decode('utf-8')
        user = User(username=username, password=stored)
        user.insert()
        return redirect(url_for('login'))


@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('username')
        passwd = request.form.get('password')
        user = User.query.filter_by(username=username).one_or_none()
        if user is None:
            flash('you do not have an account. Please signup first.')
            return redirect(url_for('signup'))

        stored = user.password
        hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),stored.encode('utf-8')[0:29])
        hashed2_str = hashed2.decode('utf-8')
        if hashed2_str != stored:
            flash('login incorrect. try again')
            return redirect( url_for('login'))

        flash('successfully logged in as '+username)
        session['username'] = username
        session['id'] = user.id
        session['logged_in'] = True
        return redirect( url_for('user', userId = user.id) )


@app.route('/newAccount', methods=["GET", "POST"])
def createAccount():
    if request.method == 'GET':
        return render_template("create_account.html")
    else:
        type = request.form.get('type')
        account = Account(type=type, money=0, uuid=str(uuid.uuid4())[:8], user_id=session['id'])
        account.insert()
        return redirect(url_for('user', userId=session['id']))


@app.route('/user/<userId>', methods=["GET", "POST"])
def user(userId):
    accounts = Account.query.filter_by(user_id=userId).order_by(Account.id.desc())
    return render_template('user.html',accounts=accounts)


@app.route('/user/deposit/<accountId>', methods=["POST"])
def deposit(accountId):
    account = Account.query.get(accountId)
    user = User.query.get(account.user_id)

    passwd = request.form['password']
    stored = user.password
    hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),stored.encode('utf-8')[0:29])
    hashed2_str = hashed2.decode('utf-8')
    if hashed2_str != stored:
        flash('Wrong password')
        return redirect(url_for("user",userId=session['id']))

    account.deposit(int(request.form.get("amount")))
    # account.updatehistory("deposit {}$")
    flash("deposit successfully")
    return redirect(url_for('user', userId=session['id']))


@app.route('/user/withdraw/<accountId>', methods=["POST"])
def withdraw(accountId):
    account = Account.query.get(accountId)
    user = User.query.get(account.user_id)

    passwd = request.form['password']
    stored = user.password
    hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),stored.encode('utf-8')[0:29])
    hashed2_str = hashed2.decode('utf-8')
    if hashed2_str != stored:
        flash('Wrong password')
        return redirect(url_for("user",userId=session['id']))

    if account.withdraw(int(request.form.get("amount"))):
        # account.updatehistory("deposit {}$")
        flash("deposit successfully")
    else:
        flash("not enough balance")
    return redirect(url_for('user', userId=session['id']))


@app.route('/user/transfer/<accountId>',methods=["POST"])
def transfer(accountId):
    fromAccount = Account.query.get(accountId)
    user = User.query.get(fromAccount.user_id)

    passwd = request.form['password']
    stored = user.password
    hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),stored.encode('utf-8')[0:29])
    hashed2_str = hashed2.decode('utf-8')
    if hashed2_str != stored:
        flash('Wrong password')
        return redirect(url_for("user",userId=session['id']))
    
    uuid = request.form.get("uuid")
    toAccount = Account.query.filter_by(uuid=uuid).one_or_none()
    if toAccount is None:
        flash('Destination account does not exists')
        return redirect(url_for("user",userId=session['id']))
    
    amount = int(request.form.get("amount"))
    if not fromAccount.withdraw(amount):
        flash("not enough balance")

    toAccount.deposit(amount)
    # fromAccount.updateHistory()
    # toAccount.updateHistory()
    flash("transfer successfully")
    return redirect(url_for("user",userId=session['id']))


@app.route('/user/delete/<accountId>',methods=["POST"])
def delete(accountId):
    account = Account.query.get(accountId)
    user = User.query.get(account.user_id)

    passwd = request.form['password']
    stored = user.password
    hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),stored.encode('utf-8')[0:29])
    hashed2_str = hashed2.decode('utf-8')
    if hashed2_str != stored:
        flash('Wrong password')
        return redirect(url_for("user",userId=session['id']))
    
    uuid = request.form.get("uuid")
    account = Account.query.filter_by(uuid=uuid).one_or_none()
    if account is None:
        flash('Wrong uuid')
        return redirect(url_for("user",userId=session['id']))
    
    if account.money > 0:
        flash('There is still money in account, please withdraw or transfer them')
        return redirect(url_for("user",userId=session['id']))

    account.delete()
    flash("delete successfully")
    return redirect(url_for("user",userId=session['id']))


if __name__ == '__main__':
    app.debug = True
    app.run()