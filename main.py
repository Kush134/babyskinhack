from flask import *
import smtplib
from email.mime.text import MIMEText
from firebase_admin import db, credentials, initialize_app, storage, auth

app = Flask(__name__)
cred_object = credentials.Certificate("static\credentials\zafado-firebase-adminsdk-key.json")
userdatabase = initialize_app(cred_object, {'databaseURL': "https://zafado-default-rtdb.firebaseio.com/", 'storageBucket': "zafado.appspot.com"})

@app.route("/")
def index():
    # return "<a href='"+url_for("signup")+"'>take me to sign up</a>"
    return render_template("index.html")

# @app.route("/testing")
# def testing():
#     data = db.reference('/')#     data.set({"name": "Ashwin", "password": "nothing123"})
#     return "done"

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if(request.method == "POST"):
        gmail = request.form['GmailId'].replace(".", "&period;")
        parent = request.form['ParentName']
        password = request.form['Password']
        cpassword = request.form['CPassword']
        if(gmail=="" or parent=="" or password==""):
            return render_template("signup.html", info1="Invalid Input", gmailvalue="")
        elif(password != cpassword):
            return render_template("signup.html", info1="password is not same", gmailvalue="")
        else:
            ref = db.reference('/user/'+gmail)
            data = ref.get()
            if(data != None):
                return render_template("signup.html", info1="Account Already Exist", gmailvalue=gmail)
            else:
                tmpUploaddata = {"parent":parent,"password":password, "days": "", "points": 0}
                ref.set(tmpUploaddata)
                return redirect(url_for('thanks', mailid=gmail.replace("&period;", ".")))
    else:
        return render_template("signup.html", gmailvalue="")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        gmail = request.form['GmailId'].replace(".", "&period;")
        password = request.form['Password']
        if(gmail == ""):
            return render_template("signin.html", info1="Invalid Input", gmailvalue="")
        else:
            ref = db.reference("/user/"+gmail)
            data = ref.get()
            if(data == None):
                return render_template("signin.html", info1="Gmail Not Found", gmailvalue=gmail)
            else:
                if(data["password"] == password):
                    return redirect(url_for('home', mailid=gmail))
                else:
                    return render_template("signin.html", info1="Incorrect Password", gmailvalue=gmail)
    else:
        return render_template("signin.html", gmailvalue="")

def sendMail(gmailid, title, msg):
    gmail_user = "emaildefault2308@gmail.com"
    gmail_pwd = "efvz tmfc oshi rdya"
    SUBJECT = title
    TEXT = msg
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_user, gmail_pwd)
    BODY = '\r\n'.join(['To: %s' % gmailid,
            'From: %s' % gmail_user,
            'Subject: %s' % SUBJECT,
            '', TEXT])
    server.sendmail(gmail_user, [gmailid], BODY)
    server.quit()

@app.route("/thanks:user=<mailid>")
def thanks(mailid):
    ref = db.reference("/user/"+mailid.replace(".", "&period;")).get()
    if(ref == None):
        return redirect(url_for("signup"))
    else:
        sendMail(mailid, "Zafado, Confirmation email your email Account", "Thanks for Signing up Zafi, Click the following link to Confirm you Account mail address.\n\nConfirmation Link: http://127.0.0.1:5000"+url_for("information", mailid=mailid))
        return render_template("thankyou.html")

@app.route("/confirmation")
def confirmtion():
    return render_template("confirmation.html")

@app.route("/information:user=<mailid>", methods=["GET", "POST"])
def information(mailid):
    if request.method == "POST":
        imageFile = request.files['profilepicture']
        babyname = request.form['babyName']
        age = request.form['age']
        gender = request.form.get('gender')
        region = request.form.get('region')
        isParent = request.form.get("isParent")
        if(isParent == None):
            isParent = False
        else:
            isParent = True
        if(imageFile.filename=='' or gender==None or region==None or babyname=="" or age == ""):
            return render_template("information.html", info="Invalid Input Data or no Profile Picture Selected")
        else:
            ref = db.reference("/user/"+mailid.replace(".", "&period;")+"/babyinfo")
            tempImagefile = request.files['profilepicture']
            tempImagefile.save("tempImagefile123.jpg")
            bucket = storage.bucket().blob(mailid.split("@")[0]+".jpg")
            bucket.upload_from_filename("tempImagefile123.jpg")
            ref.set({"babyName":babyname, "age": int(age), "gender": gender[0], "region": region, "isParent": isParent})
            return redirect(url_for('home', mailid=mailid))
    else:
        ref = db.reference("/user/"+mailid.replace(".", "&period;")+"/babyinfo").get()
        if(ref == None):
            return render_template("information.html", info="")
        else:
            return redirect(url_for("home", mailid=mailid))

@app.route("/changePassword:user=<mailid>", methods=["GET", "POST"])
def changePassword(mailid):
    if(request.method == "POST"):
        ref = db.reference("/user/"+mailid.replace(".", "&period;")+"/password")
        if(ref.get() == request.form['oldPassword']):
            newPassword = request.form['newPassword']
            cnewPassword = request.form['cnewPassword']
            if(newPassword == cnewPassword):
                ref.set(newPassword)
                return redirect(url_for('account', mailid=mailid))
            else:
                return render_template("change_password.html", mailid=mailid, info="Invalid Confirm Password")
        else:
            return render_template("change_password.html", mailid=mailid, info="Incorrect Old Password")
    else:
        return render_template("change_password.html", mailid=mailid, info="")


@app.route("/leaderboard")
def leaderboard():
    data_ref = db.reference("/user")
    top = data_ref.order_by_child('points').limit_to_last(15).get()
    print(top.values())
    return render_template("leaderboard.html", top=top)

@app.route("/doctorConsultancy")
def doctorConsultancy():
    docRef = db.reference('/doctors')
    return render_template("doctor_consultancy.html", data = docRef.get())

@app.route("/account:user=<mailid>")
def account(mailid):
    userinfo = db.reference("/user/"+mailid.replace(".", "&period;")).get()
    return render_template("account.html", userinfo=userinfo, userpoints=userinfo['points'])

@app.route("/learning:day=<day>")
def learning(day):
    ref = db.reference("/chat/day"+day+"/data").get()
    print("/chat/day"+day+"/data")
    if ref == None:
        return "Invalid Request"
    else:
        return render_template("daily_mission.html", day=day, chat=ref.split('``'))

@app.route("/quiz:question=<no>,day=<day>,mail=<mailid>", methods=['GET', 'POST'])
def quiz(no, day, mailid):
    ref = db.reference("/quiz/day"+day+"/"+no)
    questiondata = ref.get()
    if(questiondata == None):
        userPointsRef = db.reference("/user/"+mailid.replace(".", "&period;")+"/days")
        if(userPointsRef.get() == ""):
            userPointsRef.set(str(day))
        else:
            userPointsRef.set(userPointsRef.get()+","+str(day))
        return redirect(url_for('home', mailid=mailid))
    question = questiondata['question']
    option = questiondata['options'].split('``')
    return render_template("quiz.html", no=no, day=day, question=question, option=option)

@app.route("/result:question=<no>,day=<day>,option=<option1>,gmail=<gmail>", methods=["POST"])
def result(no, day, option1, gmail):
    option1 = int(option1)
    userPoints  = db.reference("/user/"+gmail.replace(".", "&period;")+"/points")
    ref = db.reference("/quiz/day"+day+"/"+no)
    questiondata = ref.get()
    question = questiondata['question']
    option = questiondata['options'].split('``')
    crtoption = db.reference("quiz/day"+day+"/"+no+"/correct").get()
    if(option1 == 0):
        return render_template("result.html", no=no, day=day, option=option, gmail=gmail,crt=crtoption, question=question, userPoints=userPoints.get())
    else:
        if(crtoption == option1):
            userPoints.set(userPoints.get()+10)
            return render_template("result.html", no=no, day=day, option=option, gmail=gmail,crt=crtoption, question=question, userPoints=userPoints.get())
        else:
            return render_template("result.html", no=no, day=day, option=option, gmail=gmail,crt=crtoption, question=question, userPoints=userPoints.get())

@app.route("/home:user=<mailid>")
def home(mailid):
    if(db.reference("/user/"+mailid.replace(".", "&period;")).get() == None):
        return redirect(url_for("signup"))
    elif(db.reference("/user/"+mailid.replace(".", "&period;")+"/babyinfo").get() == None):
        return render_template(url_for("/conformation"))
    else:
        data = db.reference("/info").get()
        userinfo = db.reference("/user/"+mailid.replace(".", "&period;")).get()
        return render_template("home.html", vidID=data['exploreVids'], userinfo=userinfo)

@app.route("/progress")
def progress():
    return render_template("progress.html")

@app.route("/queries", methods=['GET','POST'])
def queries():
    ref = db.reference("/query")
    return render_template("queries.html", data = ref.get())

@app.route("/queriesCommentPost:user=<mailid>,no=<no>,time=<time>", methods=['POST'])
def queriesCommentPost(mailid, no, time):
    if(request.method == "POST"):
        ref1 = db.reference("query/"+no+"/commentcount")
        value = ref1.get()
        print(value)
        ref1.set(value+1)
        Comment = request.form['CommentInput']
        ref = db.reference("query/"+no+"/comments/c"+str(value))
        ref.set({'name': mailid.split("@")[0], "comment": Comment, "time": time})
        return redirect(url_for("queries"))
    else:
        return "Error 403: forbidden"

@app.route("/addaquery:user=<mailid>,time=<time>", methods=['GET','POST'])
def addaquery(mailid, time):
    if(request.method == "POST"):
        data = request.form['input']
        if(data == ''):
            return render_template("addquery.html", info="Invalid Input")
        else:
            data = request.form['input']
            imageFile = request.files['profilepicture']
            hasimage = False
            ref1 = db.reference('querycount')
            countvalue = ref1.get()
            ref1.set(countvalue+1)
            if(imageFile.filename == ''):
                hasimage = False
            else:
                hasimage = True
                tempImagefile = imageFile
                tempImagefile.save("tempImagefile123.jpg")
                bucket = storage.bucket().blob('queries/q'+str(countvalue+1)+".jpg")
                bucket.upload_from_filename("tempImagefile123.jpg")
            ref2 = db.reference('/query/q'+str(countvalue+1))
            ref2.set({'commentcount':0, 'hasimage':hasimage, 'name':mailid.split('@')[0], 'question': data, 'time': time})
            return redirect(url_for('queries'))
    else:
        return render_template("addquery.html", info="")
if __name__ == '__main__':
    app.run(debug=True)
