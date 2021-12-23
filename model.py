from sqlalchemy import Column, String
from flask_sqlalchemy import SQLAlchemy
import time

database_name = "bank"
database_path = "postgresql://{}/{}".format('localhost:5432', database_name)

db = SQLAlchemy()

def setup_db(app, database_path=database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()

# def db_drop_and_create_all():
#     db.drop_all()
#     db.create_all()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(180), nullable=False)
    accounts = db.relationship("Account", backref="user", lazy=True)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(String(10))
    type = db.Column(String(10), nullable=False)
    money = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    history = db.Column(String(10000))

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def deposit(self,i):
        self.money += i
        self.update()
    
    def withdraw(self,i):
        if i <= self.money:
            self.money -= i
            self.update()
            return True
        else:
            return False

    def updateHistory(self,s):
        if self.history is None:
             self.history = (s + " at " + time.strftime("%A, %d. %B %Y %I:%M:%S %p") + ";")
        elif len(self.history)<900:
            self.history += (s + " at " + time.strftime("%A, %d. %B %Y %I:%M:%S %p") + ";")
        self.update()
