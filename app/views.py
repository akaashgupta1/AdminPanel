from app import app
from app import connect_hq_db, connect_local_db
from forms import LoginForm,ForgotPassword,PassForm, StaffForm
from flask import request, session, g, redirect, url_for, abort, render_template, flash
from flask import jsonify
import LocalHQInterface

def commit():
    g.ldb.commit()
    g.hqdb.commit()

def get_db():
    if not hasattr(g, 'ldb'):
        g.ldb = connect_local_db()
    if not hasattr(g, 'hqdb'):
        g.hqdb = connect_hq_db()
    return g

@app.before_request
def before_request():
    g.ldb = connect_local_db()
    g.hqdb = connect_hq_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'ldb', None)
    if db is not None:
        db.close()
    db = getattr(g, 'hqdb', None)
    if db is not None:
        db.close()

@app.route('/')
@app.route('/index')
def index():
    if 'username' in session:
        if('lockdown' in session):
            return render_template("index.html",title = 'Home',user = session['username'], lockdown = session['lockdown'] )
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/eod', methods = ['GET', 'POST'])
def eod():
    if 'username' in session:
        if('lockdown' in session):
            LocalHQInterface.performEOD(g.ldb.cursor(),g.hqdb.cursor())
            commit()
            return render_template("index.html",title = 'Home',user = session['username'], lockdown = session['lockdown'] )
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/sod', methods = ['GET', 'POST'])
def sod():
    if 'username' in session:
        if('lockdown' in session):
            LocalHQInterface.performSOD(g.ldb.cursor(),g.hqdb.cursor())
            commit()
            return render_template("index.html",title = 'Home',user = session['username'], lockdown = session['lockdown'] )
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/index')
    form = LoginForm()
    if form.validate_on_submit():
        staff_id = form.staffID.data
        password = form.password.data
        result = LocalHQInterface.checkShopLogin(staff_id,password,g.ldb.cursor())
        commit()
        if(result):
            session['staff_id']=staff_id;
            session['username']= LocalHQInterface.getStaffName(staff_id,g.ldb.cursor())
            commit()
            session['logged_in']= True;
            session['lockdown'] = LocalHQInterface.getStaffPermission(g.ldb.cursor())
            commit()
            if(session['lockdown']==1):
                return redirect('/locked')
            return redirect('/index')
        else:
            flash('Incorrect Username or Password')
            flash('You might not have the appropriate permissions!')
            return redirect(url_for('login'))
    return render_template('login.html',
        title = 'Sign In',
        form = form)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('staff_id', None)
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/change_pass', methods = ['GET', 'POST'])
def changepass():
    if 'username' in session:
        if('lockdown' in session):
            form = PassForm()
            if form.validate_on_submit():
                old = form.current.data
                new = form.password.data
                confirm = form.confirm.data
                if(new!=confirm):
                    flash('Passwords do not match.')
                    return render_template('change-password.html',user = session['username'],title = 'Change Password',form = form)
                result = LocalHQInterface.changePassword(session['staff_id'],old,new,g.ldb.cursor())
                commit()
                if(not result):
                    flash('You entered the old password incorrectly.')
                    return render_template('change-password.html',user = session['username'],title = 'Change Password',form = form)
                return redirect('/index')
            return render_template('change-password.html',
                title = 'Change Password',
                user = session['username'],
                form = form)
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/forgot_pass', methods = ['GET', 'POST'])
def forgot():
    form = ForgotPassword()
    if form.validate_on_submit():
        id = form.staffID.data
        email = form.email.data
        result = LocalHQInterface.resetPassword(id,email,g.ldb.cursor())
        commit()
        if(result == False):
            flash('Incorrect ID Entered.')
            return render_template('forgot_password.html', title = 'Reset Password',form = form)
        flash('Your new password has been sent to your email.')
        return redirect('/login')
    return render_template('forgot_password.html',
        title = 'Reset Password',
        form = form)

@app.route('/products', methods = ['GET', 'POST'])
def products():
    if 'username' in session:
        if('lockdown' in session):
            list = LocalHQInterface.getListOfProducts(g.ldb.cursor())
            return render_template("inventory.html", title = 'Inventory',user = session['username'], lockdown = session['lockdown'], list= list)
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/transaction', methods = ['GET', 'POST'])
def transaction():
    if 'username' in session:
        if('lockdown' in session):
            userlist = LocalHQInterface.getListOfStaffID(g.ldb.cursor())
            list = LocalHQInterface.getListOfTransactions(g.ldb.cursor())
            commit()
            return render_template("transaction.html",title = 'Transaction History',user = session['username'], lockdown = session['lockdown'], list=list,userlist=userlist)
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

#@app.route('/products_search', methods = ['GET', 'POST'])
#def product_search():
#    if 'username' in session:
#        if('lockdown' in session):
#            return render_template("p_search.html",title = 'Product Search',user = session['username'], lockdown = session['lockdown'])
#        else:
#            return  redirect('/login')
#    else:
#        return redirect(url_for('login'))
#
#@app.route('/trans_search', methods = ['GET', 'POST'])
#def transaction_search():
#    if 'username' in session:
#        if('lockdown' in session):
#            return render_template("t_search.html",title = 'Transaction Search',user = session['username'], lockdown = session['lockdown'])
#        else:
#            return  redirect('/login')
#    else:
#        return redirect(url_for('login'))

@app.route('/trans_add', methods = ['GET', 'POST'])
def add_transaction():
    if 'username' in session:
        if('lockdown' in session):
            if request.method == 'POST':
                staffID = request.form['staff']
                setCount = request.form['Count']
                barlist=[]
                qualist = []
                for i in range(int(setCount)):
                    barlist.append(str(request.form['Barcodes'+str(i+1)]))
                    qualist.append(str(request.form['Quantities'+str(i+1)]))
                result = LocalHQInterface.addTransactionToLocal(staffID,barlist,qualist,g.ldb.cursor())
                commit()
                return jsonify({'result': result})
            userlist = LocalHQInterface.getListOfStaffID(g.ldb.cursor())
            list = LocalHQInterface.getListOfTransactions(g.ldb.cursor())
            commit()
            return render_template("transaction.html",title = 'Transaction History',user = session['username'], lockdown = session['lockdown'], list=list,userlist=userlist)
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/staff', methods = ['GET', 'POST'])
def staff():
    form = StaffForm()
    if 'username' in session:
        if('lockdown' in session):
            if form.validate_on_submit():
                address = form.address.data
                contacts = form.contact.data
                dob = form.dob.data
                gender = form.gender.data
                name = form.name.data
                t_pass = form.temp_pass.data
                print (address,contact,dob,gender,name,t_pass)
                result = LocalHQInterface.createNewUser(address,contacts,dob,gender,name,t_pass,g.ldb.cursor(),g.hqdb.cursor())
                if result:
                    commit()
                    list = LocalHQInterface.getListOfStaff(g.ldb.cursor())
                    return render_template("staff.html",title = 'Staff in Store',user = session['username'], lockdown = session['lockdown'],list = list, form = form, click = '2')
                list = LocalHQInterface.getListOfStaff(g.ldb.cursor())
                return render_template("staff.html",title = 'Staff in Store',user = session['username'], lockdown = session['lockdown'],list = list, form = form, click = '1')
            elif(form.is_submitted() and not(form.validate_on_submit())):
                list = LocalHQInterface.getListOfStaff(g.ldb.cursor())
                return render_template("staff.html",title = 'Staff in Store',user = session['username'], lockdown = session['lockdown'],list = list, form = form, click = '1')
            list = LocalHQInterface.getListOfStaff(g.ldb.cursor())
            return render_template("staff.html",title = 'Staff in Store',user = session['username'], lockdown = session['lockdown'],list = list, form = form, click = '0')
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/contacts', methods = ['GET', 'POST'])
def contact():
    if 'username' in session:
        if('lockdown' in session):
            return render_template("contact.html",title = 'Contact HeadQuarters',user = session['username'], lockdown = session['lockdown'])
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))


@app.route('/locked', methods = ['GET', 'POST'])
def locked():
    if 'username' in session:
        if('lockdown' in session):
            if(session['lockdown'] == 0):
                LocalHQInterface.lockdownPermission(g.ldb.cursor())
                commit()
                session['lockdown'] = 1
            return render_template("lockdown.html",title = 'Lockdown Initiated',user = session['username'], lockdown = session['lockdown'])
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.route('/release_lockdown', methods = ['GET', 'POST'])
def release():
    if 'username' in session:
        if('lockdown' in session):
            if (session['lockdown'] == 1):
                LocalHQInterface.releasePermission(g.ldb.cursor())
                commit()
                session['lockdown'] = 0
            return render_template("release.html",title = 'Lockdown Released',user = session['username'], lockdown = session['lockdown'])
        else:
            return  redirect('/login')
    else:
        return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404