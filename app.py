from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
app=Flask(__name__)
app.secret_key="jiya@123"
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///itsm_ticket_resolution.db"
app.config['SQLALCHEMY_BINDS'] = {    
    'ticket_db': 'sqlite:///ticket.db'
}
db=SQLAlchemy(app)
class User(db.Model):
    username=db.Column(db.String(200),primary_key=True)
    password=db.Column(db.String(200),nullable=False)

class Ticket(db.Model):
    TicketNumber=db.Column(db.Integer,primary_key=True,autoincrement=True)
    UserEmail=db.Column(db.String(200))
    shortDesc=db.Column(db.String(200),nullable=False)
    longDesc=db.Column(db.String(200))
    IssueType=db.Column(db.String(10))
    Priority=db.Column(db.String(10))


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login',methods=['POST','GET'])
def login_page():
    if request.method=='POST':
        session['useremail']=request.form['useremail'] # we basically store the useremail in our session so that we can use it further while calling /mytickets sort of API
        print(session)
        return redirect('/welcome')
    return render_template('login.html')

#creating landing page endpoint
@app.route('/welcome')
def welcome_page():
    return render_template('welcome.html')

@app.route('/raise_ticket',methods=['GET','POST'])
def raise_ticket():    
    if(request.method=='POST'):
        __bind_key__ = 'ticket_db'
        shortDesc=request.form['shortDesc']
        longDesc=request.form['longDesc']
        UserEmail=session['useremail']
        print(shortDesc)
        print(longDesc)  
        ticket=Ticket(shortDesc=shortDesc,longDesc=longDesc,UserEmail=UserEmail)
        print(ticket)
        db.session.add(ticket)
        db.session.commit()
        print("Count: ",Ticket.query.count())
        for t in Ticket.query.all():
            print(t.shortDesc)
    return render_template('raise_ticket.html')

@app.route('/my_tickets')
def fetch_my_tickets():
    return render_template("my_tickets.html")

with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(debug=True,port=5001)