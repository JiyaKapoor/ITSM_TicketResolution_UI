from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app=Flask(__name__)
app.secret_key="jiya@123" # used to cryptographically sign the user session key 
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://postgres:jiya123@localhost:5432/itsm_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)

class User(db.Model):
    username=db.Column(db.String(200),primary_key=True)
    password=db.Column(db.String(200),nullable=False)
    role=db.Column(db.String(20),nullable=False) # a user maybe admin or User 

class Ticket(db.Model):
    TicketNumber=db.Column(db.Integer,primary_key=True,autoincrement=True)
    UserEmail=db.Column(db.String(200))
    shortDesc=db.Column(db.String(200),nullable=False)
    longDesc=db.Column(db.String(200))
    IssueType=db.Column(db.String(10))
    Priority=db.Column(db.String(10))
    Status=db.Column(db.String(20))
    AssignedTo=db.Column(db.String(50))
    CreatedAt=db.Column(db.DateTime)
    Resolution=db.Column(db.String(500))

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login',methods=['POST','GET'])
def login_page():
    if request.method=='POST':
        session['useremail']=request.form['useremail'] # we basically store the useremail in our session so that we can use it further while calling /mytickets sort of API
        print(session)
        return redirect('/welcome') # here is the request is a POST request then the user will be redirected to the welcome page (since POST req means that user has submitted the login form)
    return render_template('login.html')

#creating landing page endpoint
@app.route('/welcome')
def welcome_page():
    return render_template('welcome.html')

@app.route('/raise_ticket',methods=['GET','POST'])
def raise_ticket():    
    if(request.method=='POST'):     
        shortDesc=request.form['shortDesc']
        longDesc=request.form['longDesc']
        issueType=request.form['issueType']
        priority=request.form['priority'] # all these fields shortDesc, longDesc are coming populated from the frontend 
        UserEmail=session['useremail'] # user email is taken from the current session only 
        print(shortDesc)
        print(longDesc)  
        ticket=Ticket(shortDesc=shortDesc,longDesc=longDesc,UserEmail=UserEmail,IssueType=issueType,Priority=priority,Status="OPEN",CreatedAt=datetime.now())
        print(ticket)
        db.session.add(ticket)
        db.session.commit()
        print("Count: ",Ticket.query.count())
        for t in Ticket.query.all():
            print(t.shortDesc)
    return render_template('raise_ticket.html')

@app.route('/my_tickets')
def fetch_my_tickets():
    # we now need to query the database to fetch tickets with the required user email id 
    email=session['useremail']
    tickets=Ticket.query.filter_by(UserEmail=email).all()
    return render_template("my_tickets.html",tickets=tickets)#we are sending the filtered tickets to the frontend via the render_template method 

with app.app_context():
    print(db.engine.url)
    print(db.metadata.tables.keys())
    db.create_all()

if __name__=="__main__":
    app.run(debug=True,port=5001)