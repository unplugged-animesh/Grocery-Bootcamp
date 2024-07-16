from sqlalchemy import or_
from flask import Flask, render_template, request, redirect, url_for, flash, session
from Models.model import *
from sqlalchemy.exc import IntegrityError
from datetime import datetime


app=Flask(__name__)
app.config['SECRET_KEY']='East'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///grocery.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICAIONS']=False
app.config['SQLALCHMEY_SILENCE_UBER_WARNING']=1


db.init_app(app)



with app.app_context():
    db.create_all()


@app.route('/',methods=['GET'])
def home():
    return redirect(url_for('logout'))



@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=="POST":
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        admin=False
        
        if request.form.get('admin_key')=="Asharma":
            admin=True           


        try:
            user=User(username=username,email=email,password=password,admin=admin)
            db.session.add(user)
            db.session.commit()
            if not admin:
                cart=Cart(user_id=user.id)
                db.session.add(cart)
                db.session.commit()
            flash('Your account is created successfully','success')
            return redirect(url_for('login'))
        
        except IntegrityError as e:
            db.session.rollback()
            flash('Username or email already exists.Please choose a different username or email')
            return redirect(url_for('signup'))
        
    return render_template('signup.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username_or_email=request.form['username']
        password=request.form['password']
        
        user=User.query.filter(
            or_(User.username== username_or_email, User.email== username_or_email)).first()
        
        if user and user.password==password:
            session['user_id']=user.id
            return redirect(f'/dashboard/{user.id}')
        else:
            error_message='Invalid Username or Password'
            if not user:
                error_message='No user fourd with the provided username or email.'
            return render_template('login.html',error_message=error_message)
        
    return render_template('login.html')    


def get_user_admin(curr_login_id):
    if 'user_id' in session and curr_login_id==session['user_id']:
        user=User.query.get(curr_login_id)
        return user.admin
    return False
    
    
    



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(port=5500)