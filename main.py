from flask import Flask, render_template,flash, redirect, url_for, session, request, logging
import pymysql.cursors
from google.cloud import storage
import os
import datetime

import re
from flask_bcrypt import Bcrypt
app = Flask(__name__)
app.secret_key = "Secret"
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=""

connection = pymysql.connect(host='',

                                 user='',
                                 password='',
                                 db='',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

bcrypt = Bcrypt(app)


cur=connection.cursor();



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def showSignUp():
    return render_template('register.html')

@app.route('/login')
def showLogin():

    return render_template('login.html')

@app.route('/access_granted', methods=['GET','POST'])
def access_granted():

        if request.method=='POST':
            username=request.form['username']
            password_received=request.form['password']

            cur = connection.cursor()
            cur.execute("Select * from Members where username =%s",[username])
            result = cur.fetchall()

            # print(password_received)
            if len(result) == 0:
                print("credentials not matched")
            else:


                password_fetched = result[0]['password']
                print(password_fetched)
                if result[0]['isactive']==1:
                    session["user"] = username
                    session["isactive"]='true'
                else:
                    print("dont ")
                    return redirect('login')
                if result[0]['isadmin']==1:
                    session["isadmin"]='true'
                    return redirect('admin')
                if bcrypt.check_password_hash(password_fetched,password_received):
                    print("matched")

                else:
                    print("not matched")

            return redirect('/display')


@app.route('/logout')
def logout():
    session.pop("user",None)
    print("session dropped")
    return render_template('index.html')

@app.route('/admin')
def admin():
    cur = connection.cursor();
    cur.execute("Select * from Members where isadmin ='0' and isactive='0' ")
    data=cur.fetchall()
    cur.execute("select * from Members where isactive='1' and isadmin='0'")
    rows = cur.fetchall()
    cur.execute("select * from Group_List where isapproved ='0'")
    result=cur.fetchall()

    cur.execute("select * from Group_List where isapproved ='1'")
    new_result=cur.fetchall()

    return render_template("admin.html",data=data,rows=rows,result=result,new_result=new_result)

@app.route('/add', methods=['GET','POST'])
def add():
    username = request.form['add']
    print(username)
    cur = connection.cursor()
    cur.execute("Update Members set isactive='1' where username=%s",[username])
    print("executed")
    connection.commit()

    return redirect('/admin')
@app.route('/add_group', methods=['GET','POST'])
def add_group():
    name = request.form['add_group']

    cur = connection.cursor()
    cur.execute("Update Group_List set isapproved='1' where name=%s",[name])
    print("executed")
    connection.commit()

    return redirect('/admin')


@app.route('/for_delete', methods=['GET','POST'])
def for_delete():
    name=request.form['name']
    cur=connection.cursor()
    cur.execute("Select * from images where group_name=%s",[name])
    data=cur.fetchall()
    return render_template('for_delete.html',data=data)
@app.route('/delete_file',methods=['GET','POST'])
def delete_file():
    # name=request.form['delete_file']
    id=request.form['delete_file']
    cur=connection.cursor()
    if cur.execute("Delete from images where id=%s",[id]):
        print("yes")
    else:
        print("no")

    connection.commit()
    return redirect('/admin')


@app.route('/delete_group', methods=['GET','POST'])
def delete_group():
    name = request.form['delete_group']
    cur=connection.cursor()
    cur.execute("Delete from Group_List where name=%s",[name])
    connection.commit()
    return redirect('/admin')
@app.route('/quit_group', methods=['GET','POST'])
def quit_group():
    group_name=request.form['quit_group']
    cur=connection.cursor()
    cur.execute("Delete from groups where group_name=%s",[group_name])
    connection.commit()
    return redirect('/display')
@app.route('/create_group', methods=['GET','POST'])
def create_group():
    username=session["user"]
    name = request.form['name']
    cur=connection.cursor()
    cur.execute("Insert into Group_List(name,username) values (%s,%s)",(name,username))
    connection.commit()
    return redirect('/display')

@app.route('/display', methods=['GET','POST'])
def display():
    if ("user" in session):
        username=session["user"]
    cur.execute("Select * from groups where username =%s", [username])
    data = cur.fetchall()
    print("hello")
    cur.execute("select * from Group_List where isapproved='1'")
    rows = cur.fetchall()
    print("got it")
    return render_template('mygroup.html',data=data,rows=rows)


@app.route('/join_group', methods=['POST'])
def join_group():
    cur = connection.cursor();
    if ("user" in session):
        username=session["user"]
        print(username)
        name = request.form['name']
        result=cur.execute("Insert into groups(group_name,username)values (%s,%s)",(name,username))
        connection.commit()
        print(result)
        cur.execute("Select * from groups where username =%s", [username])
        data = cur.fetchall()
        cur.execute("select * from Group_List where isapproved='1'")
        rows = cur.fetchall()

        if result:
            print("inserted")

        return render_template('mygroup.html',data=data,rows=rows)


@app.route('/signup',methods=['POST','GET'])
def register():
    if request.method == "POST":
        username = request.form['username']

        if len(username) < 5 or len(username) > 80:
            flash("Username must be between 5 and 80 characters")
            return render_template('register.html')
        name = request.form['name']
        if len(name) < 5 or len(name) > 20:
            flash("Username must be between 5 and 20 characters")
            return render_template('register.html')

        password=request.form['password']
        if not re.match(r'[A-Za-z0-9@#$%^&+=]{8,}',password):
            flash("Please enter 8 charachter long password")
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password)


    print(hashed_password)
    cur.execute("Insert INTO Members(username,name,password)values (%s,%s,%s)",(username,name,hashed_password))
    connection.commit()
    print("here")
    flash('You are now registered and can log in', 'success')
    return render_template('index.html')

@app.route('/download',methods=['POST','GET'])
def download():
    name = request.form['name']
    print(name)
    cur = connection.cursor()
    cur.execute("Select * from images where group_name =%s", [name])
    data=cur.fetchall()

    return render_template('images.html',data=data)
@app.route('/delete_member',methods=['POST','GET'])
def delete_member():
    name=request.form['delete']
    cur=connection.cursor()
    cur.execute("Delete from Members where username=%s",[name])
    connection.commit()

    return redirect ('/admin')

@app.route('/upload', methods=['POST'])
def upload():

    file = request.files['image']
    name = request.form['name']
    description = request.form['description']
    time = datetime.datetime.now().time()
    date = datetime.datetime.now().date()
    print("time", time)

    print(name)
    upload_blob('secureprogramming',file,file.filename)
    base_url=''
    file_url = base_url+ file.filename
    print(file_url)
    cur=connection.cursor()
    cur.execute("Insert into images(group_name,url,description,date,time)values(%s,%s,%s,%s,%s) ",(name,file_url,description,date,time))
    connection.commit()
    flash("File uploaded")
    return redirect('/display')

def upload_blob(bucket_name, source_file_name, destination_blob_name):
        """Uploads a file to the bucket."""
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_file(source_file_name)

        print('File {} uploaded to {}.'.format(
            source_file_name,
            destination_blob_name))


if __name__ == '__main__':
   app.run(debug=True)
