from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String(50),unique=True,nullable=False)
    email=db.Column(db.String(),unique=True,nullable=False)
    password=db.Column(db.String(50),nullable=False)
    admin=db.Column(db.Boolean(),nullable=False)
    
    
class Category(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.String(50),unique=True,nullable=False)
    products=db.relationship("Product", backref="Category", lazy=True, cascade="all,delete-orphan")
    
class Product(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.String(50),unique=True,nullable=False)
    price=db.Column(db.Float,nullable=False)
    mf_date=db.Column(db.Date,nullable=False)
    expiry_date=db.Column(db.Date,nullable=False)
    
    
        
    