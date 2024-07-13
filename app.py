from sqlalchemy import or_
from Models.model import *
from flask import Flask,render_template,request


app=Flask(__name__)
app.config['SECRET_KEY']='East'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///grocery.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICAIONS']=False
app.config['SQLALCHMEY_SILENCE_UBER_WARNING']=1


db.init_app(app)



with app.app_context():
    db.create_all()
    
    
    