from flask import (Flask, render_template, url_for, redirect, request, flash, session)
from flask_cors import CORS
from model import setup_db, User, Account
import bcrypt
import random
import uuid
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
setup_db(app)
CORS(app)
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +'abcdefghijklmnopqrstuvxyz' +'0123456789')) for i in range(20) ])


@app.route('/')
def index():
    return redirect_()   


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
        return redirect_()


@app.route('/newAccount', methods=["GET", "POST"])
def createAccount():
    if request.method == 'GET':
        return render_template("create_account.html")
    else:
        type = request.form.get('type')
        if 'id' not in session:
            return redirect_()
        else:
            account = Account(type=type, money=0, uuid=str(uuid.uuid4())[:8], user_id=session['id'])
            account.insert()
            account.updateHistory("create account")
        return redirect_()


@app.route('/user', methods=["GET", "POST"])
def user():
    userId = session['id']
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
        return redirect_()

    amount = int(request.form.get("amount"))
    account.deposit(amount)
    account.updateHistory("deposit {}$".format(amount))
    flash("deposit successfully")
    return redirect_()


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
        return redirect_()

    amount = int(request.form.get("amount"))
    if account.withdraw(amount):
        account.updateHistory("withdraw {}$".format(amount))
        flash("deposit successfully")
    else:
        flash("not enough balance")
    return redirect_()


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
        return redirect_()
    
    uuid = request.form.get("uuid")
    toAccount = Account.query.filter_by(uuid=uuid).one_or_none()
    if toAccount is None:
        flash('Destination account does not exists')
        return redirect_()
    
    amount = int(request.form.get("amount"))
    if not fromAccount.withdraw(amount):
        return flash("not enough balance")

    toAccount.deposit(amount)
    fromAccount.updateHistory("transfer {}$ to account {}".format(amount,uuid))
    toAccount.updateHistory("receive {}$ from account {}".format(amount,fromAccount.uuid))
    flash("transfer successfully")
    return redirect_()


@app.route('/user/history/<accountId>')
def history(accountId):
    account = Account.query.get(accountId)
    return account.history


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
        return redirect_()
    
    uuid = request.form.get("uuid")
    account = Account.query.filter_by(uuid=uuid).one_or_none()
    if account is None:
        flash('Wrong uuid')
        return redirect_()
    
    if account.money > 0:
        flash('There is still money in account, please withdraw or transfer them')
        return redirect_()

    account.delete()
    flash("delete successfully")
    return redirect_()


def gain_interest():
    for account in Account.query.all():
        if account.money < 1000000000:
            if account.type == "checking":
                amount = account.money * 0.5
            else:
                amount = account.money * 1
            account.deposit(amount)
            account.updateHistory("Gain {}$ Interest".format(amount))


def redirect_():
    if 'id' in session:
        return redirect(url_for('user'))
    else:
        return redirect(url_for('login'))


scheduler = BackgroundScheduler()
scheduler.add_job(func=gain_interest, trigger="interval", seconds=60)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    app.debug = True
    app.run()