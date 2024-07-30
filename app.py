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



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        admin = False  
        
        
        if request.form.get('admin_key') == 'Asharma':
            admin = True

        try:
            user = User(username=username, email=email,password=password, admin=admin)
            db.session.add(user)
            db.session.commit()
            if not admin:
                cart = Cart(user_id=user.id)
                db.session.add(cart)
                db.session.commit()
            flash('Your account was created successfully.', 'success')
            return redirect(url_for('login'))

        except IntegrityError as e:
            db.session.rollback()
            flash('Username or email already exists. Please choose a different username or email.')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        user = User.query.filter(
            or_(User.username == username_or_email, User.email == username_or_email)).first()

        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(f'/dashboard/{user.id}')
        else:
            error_message = 'Invalid Username or Password'
            if not user:
                error_message = 'No user found with the provided username or email.'
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

def get_user_admin(curr_login_id):
    if 'user_id' in session and curr_login_id == session['user_id']:
        user = User.query.get(curr_login_id)
        return user.admin
    return False


@app.route('/dashboard/<int:curr_login_id>',methods=['GET'])
def dashboard(curr_login_id):
    if request.method == 'GET':
        if 'user_id' in session and session['user_id']== curr_login_id:
            user= User.query.get(curr_login_id)
            if user.admin:
                return redirect(url_for('admin_dashboard',curr_login_id=curr_login_id))
            else:
                return redirect(url_for('customer_dashboard',curr_login_id=curr_login_id))
            
        flash('Please login to access the dashboard')
        return redirect (url_for('logout'))
    
  
        
@app.route('/admin/<int:curr_login_id>/dashboard',methods=['GET'])
def admin_dashboard(curr_login_id):
    if request.method =='GET':
        if 'user_id' in session and session['user_id'] == curr_login_id:
            user=User.query.get(curr_login_id)
            if not user.admin:
                return redirect(f"/dashboard/{curr_login_id}")
            
            categories=Category.query.all()
            data={'curr_login_id': curr_login_id,
                  'categories': categories}
            
            return render_template('admin_dashboard.html',data=data,name=User.query.get(curr_login_id).username)
        
        flash('Please login to acess the admin dashboard')
        return redirect(url_for('logout'))
    
    
@app.route('/admin/<int:curr_login_id>/stats',methods=['GET'])
def admin_stats(curr_login_id):
    if 'user_id' in session and session['user_id']==curr_login_id:
        user=User.query.get(curr_login_id)
        if not user.admin:
            flash('Not Allowed')
            return redirect(f'/dashboard/{curr_login_id}')
        
        categories=Category.query.all()
        category_stats=[]
        for category in categories:
            product_count=len(category.products)
            total_quantity=sum([product.quantity for product in category.products])
            category_stats.append({
                'name':category.name,
                'product_count':product_count,
                'total_quantity':total_quantity
                
            })
        data={
            'curr_login_id':curr_login_id,
            'category_stats':category_stats
        }
        return render_template('admin_stats.html',data=data,name=user.username)
    return redirect(url_for('logout'))
        
    
@app.route('/customer/<int:curr_login_id>/dashboard', methods=['GET'])
def customer_dashboard(curr_login_id):
    if request.method == 'GET':
        if 'user_id' in session and session['user_id'] == curr_login_id:
            categories = Category.query.all()
            user_cart = Cart.query.filter_by(user_id=curr_login_id).first()
            data = {'curr_login_id': curr_login_id,
                    'cart': {f'{category.name}': [((lambda x: 0 if x is None else x.quantity)(CartItem.query.filter_by(
                        cart_id=user_cart.id, cartitem_product_id=product.id).first()), product) for product in category.products] for category in categories}}
            return render_template('customer_dashboard.html', data=data, name=User.query.get(curr_login_id).username)
        flash('Please login to access the admin dashboard.')
        return redirect(url_for('logout'))

@app.route('/admin/<int:curr_login_id>/create_category',methods=['GET',"POST"])
def create_category(curr_login_id):
    if not get_user_admin(curr_login_id):
        flash("You are not authorised to access this page.")
        return redirect(url_for('logout'))
    
    if request.method=='POST':
        name=request.form['name']
        
        try:
            category=Category(name=name)
            db.session.add(category)
            db.session.commit()
            return redirect(url_for('admin_dashboard',curr_login_id=curr_login_id))
        
        except IntegrityError:
            db.session.rollback()
            flash('category with the given name already exists.')
            return redirect(url_for('create_category',curr_login_id=curr_login_id))
        
    return render_template('create_category.html',curr_login_id=curr_login_id)    


@app.route('/admin/<int:curr_login_id>/edit_category/<int:category_id>',methods=['GET',"POST"])
def edit_category(curr_login_id,category_id):
    if not get_user_admin(curr_login_id):
        flash("You are not authorised to access this page.")
        return redirect(url_for('logout'))
    
    category=Category.query.get_or_404(category_id)
    
    if request.method=='POST':
        
        try:
            category.name=request.form['name']
            db.session.commit()
            flash('Category Updated Successfully')
            return redirect(url_for('edit_category',curr_login_id=curr_login_id,category_id=category.id))
        
        except IntegrityError:
            db.session.rollback()
            flash('category with the given name already exists.')
            return redirect(url_for('edit_category',curr_login_id=curr_login_id,category_id=category.id))
        
    return render_template('edit_category.html',curr_login_id=curr_login_id,category=category)    



@app.route('/admin/<int:curr_login_id>/remove/<int:category_id>', methods=['GET', 'POST'])
def remove_category(curr_login_id, category_id):
    if not get_user_admin(curr_login_id):
        flash('You are not authorized to access this page.')
        return redirect(url_for('logout'))

    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        db.session.delete(category)
        db.session.commit()
        return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

    return render_template('remove_category.html', curr_login_id=curr_login_id, category=category)

@app.route('/admin/<int:curr_login_id>/create_product', methods=['GET','POST'])
def create_product(curr_login_id):
    if not get_user_admin(curr_login_id):
        flash("You are not authorised to access this page.")
        return redirect(url_for('logout'))
    
    if request.method=='POST':
        name=request.form['name']
        price=float(request.form['price'])
        unit=request.form['unit']
        quantity=int(request.form['quantity'])
        mf_date=datetime.strptime(request.form['mf_date'],'%Y-%m-%d').date()
        expiry_date=datetime.strptime(request.form['expiry_date'],'%Y-%m-%d').date()
        category_id=int(request.form['category_id'])
        
        product=Product(
            name=name,
            price=price,
            unit=unit,
            quantity=quantity,
            mf_date=mf_date,
            expiry_date=expiry_date,
            category_id=category_id
        )
        try:
            db.session.add(product)
            db.session.commit()
            return redirect(url_for('admin_dashboard',curr_login_id=curr_login_id))
        
        except IntegrityError:
            db.session.rollback()
            flash('Product already exists.')
            return redirect(url_for('create_product',curr_login_id=curr_login_id))
        
    categories=Category.query.all()    
    return render_template('create_product.html',curr_login_id=curr_login_id,categories=categories)    

    
@app.route('/admin/<int:curr_login_id>/edit_product/<int:product_id>', methods=['GET','POST'])
def edit_product(curr_login_id,product_id):
    if not get_user_admin(curr_login_id):
        flash("You are not authorised to access this page.")
        return redirect(url_for('logout'))
    
    product=Product.query.get_or_404(product_id)
    
    if request.method=='POST':
        product.name=request.form['name']
        product.price=float(request.form['price'])
        product.unit=request.form['unit']
        product.quantity=int(request.form['quantity'])
        product.mf_date=datetime.strptime(request.form['mf_date'],'%Y-%m-%d').date()
        product.expiry_date=datetime.strptime(request.form['expiry_date'],'%Y-%m-%d').date()
        product.category_id=int(request.form['category_id'])
        
        
        try:
            db.session.commit()
            return redirect(url_for('admin_dashboard',curr_login_id=curr_login_id))
        
        except IntegrityError:
            db.session.rollback()
            flash('Product already exists.')
            return redirect(url_for('edit_product',curr_login_id=curr_login_id,product_id=product_id))
        
    categories=Category.query.all()    
    return render_template('edit_product.html',curr_login_id=curr_login_id,categories=categories,product=product)    

        
@app.route('/admin/<int:curr_login_id>/remove_product/<int:product_id>', methods=['GET', 'POST'])
def remove_product(curr_login_id, product_id):
    if not get_user_admin(curr_login_id):
        flash('You are not authorized to access this page.')
        return redirect(url_for('logout'))

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('admin_dashboard', curr_login_id=curr_login_id))

    return render_template('remove_product.html', curr_login_id=curr_login_id,product=product)

        
@app.route('/customer/<int:curr_login_id>/product/<int:product_id>/add-to-cart', methods=['GET', 'POST'])
def customer_add_to_cart(curr_login_id, product_id):
    if 'user_id' not in session or curr_login_id != session['user_id']:
        flash('Current session logged out!')
        return redirect(url_for('logout'))

    product = Product.query.get_or_404(product_id)
    quantity = int(request.form['quantity'])
    cart = Cart.query.filter_by(user_id=curr_login_id).first()
    existing_quantity = 0
    found = False
    for item in cart.items:
        if product.id == item.cartitem_product_id:
            existing_quantity = item.quantity
            found = True
            break
    if product.quantity >= quantity+existing_quantity:
        if not found:
            cart_item = CartItem(
                cart_id=cart.id, quantity=quantity, cartitem_product_id=product_id)
            db.session.add(cart_item)
            cart.cart_count += 1
        else:
            item.quantity += quantity
        db.session.commit()

    return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))


@app.route('/customer/<int:curr_login_id>/cart', methods=['GET'])
def cart(curr_login_id):
    if 'user_id' not in session or curr_login_id != session['user_id']:
        flash('Current session logged out!')
        return redirect(url_for('logout'))

    cart = Cart.query.filter_by(user_id=curr_login_id).first()
    cartitem_pdt = [(item, Product.query.get(item.cartitem_product_id))
                    for item in cart.items]

    data = {'cartitem_pdt': cartitem_pdt, 'isEmpty': True if len(cartitem_pdt) == 0 else False,
            'amount': sum(Product.query.get(item.cartitem_product_id).price *
                          min(item.quantity, Product.query.get(item.cartitem_product_id).quantity) for item in cart.items), 'curr_login_id': curr_login_id}

    return render_template('cart.html', data=data, name=User.query.get(curr_login_id).username)


@app.route('/customer/<int:curr_login_id>/cart/<int:product_id>/edit', methods=['POST'])
def update_cart_quantity(curr_login_id, product_id):
    if 'user_id' not in session or curr_login_id != session['user_id']:
        flash('Current session logged out!')
        return redirect(url_for('logout'))

    cart_item = CartItem.query.filter_by(
        cartitem_product_id=product_id).first()

    if not cart_item:
        flash('Product not found in cart.')
        return redirect(url_for('cart', curr_login_id=curr_login_id))

    product = Product.query.get(cart_item.cartitem_product_id)
    new_quantity = int(request.form['quantity'])

    if new_quantity <= product.quantity:
        cart_item.quantity = new_quantity
        db.session.commit()

    return redirect(url_for('cart', curr_login_id=curr_login_id))


@app.route('/customer/<int:curr_login_id>/cart/<int:product_id>/remove-cartitem', methods=['POST'])
def remove_from_cart(curr_login_id, product_id):
    if 'user_id' not in session or curr_login_id != session['user_id']:
        flash('Current session logged out!')
        return redirect(url_for('logout'))

    cart_item = CartItem.query.filter_by(
        cartitem_product_id=product_id).first()

    if not cart_item:
        flash('Product not found in cart.')
        return redirect(url_for('cart', curr_login_id=curr_login_id))

    db.session.delete(cart_item)
    db.session.commit()

    flash('Product removed from cart and quantity added back.')
    return redirect(url_for('cart', curr_login_id=curr_login_id))


@app.route('/customer/<int:curr_login_id>/checkout', methods=['GET', 'POST'])
def checkout(curr_login_id):
    if 'user_id' not in session or curr_login_id != session['user_id']:
        flash('Current session logged out!')
        return redirect(url_for('logout'))

    cart = Cart.query.filter_by(user_id=curr_login_id).first()
    cartitem_pdt = [(item, Product.query.get(item.cartitem_product_id))
                    for item in cart.items if Product.query.get(item.cartitem_product_id).quantity > 0]
    data = {'cartitem_pdt': cartitem_pdt, 'isEmpty': True if len(cartitem_pdt) == 0 else False,
            'amount': sum(Product.query.get(item.cartitem_product_id).price *
                          min(item.quantity, Product.query.get(item.cartitem_product_id).quantity) for item in cart.items), 'curr_login_id': curr_login_id, 'isEmpty': True if len(cartitem_pdt) == 0 else False}
    if request.method == 'POST':

        db.session.commit()

        for item in cart.items:
            product = Product.query.get(item.cartitem_product_id)
            product.quantity -= item.quantity
            product.sold_quantity += item.quantity

        db.session.delete(cart)
        cart = Cart(user_id=curr_login_id)
        db.session.add(cart)
        db.session.commit()

        return redirect(url_for('customer_dashboard', curr_login_id=curr_login_id))

    return render_template('checkout.html', data=data)


@app.route('/customer/<int:curr_login_id>/search', methods=['GET', 'POST'])
def search(curr_login_id):
    if request.method=="POST":
        search_query=request.form['search']
        products=Product.query.filter(
            Product.name.ilike(f'%{search_query}%')
        ).all()
        categories=Category.query.filter(
            Category.name.ilike(f'%{search_query}%')
        ).all()
        
        return render_template('search.html',curr_login_id=curr_login_id,search_query=search_query,products=products,categories=categories)
    return redirect(url_for('home'))
    



















@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(port=5500)