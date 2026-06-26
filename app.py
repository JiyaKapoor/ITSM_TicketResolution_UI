from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,or_
from datetime import datetime
from datetime import date,timedelta
app=Flask(__name__)
app.secret_key="jiya@123" # used to cryptographically sign the user session key 
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://postgres:jiya123@localhost:5432/itsm_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)

class User(db.Model):
    username=db.Column(db.String(200),primary_key=True)
    password=db.Column(db.String(200),nullable=False)
    role=db.Column(db.String(20),nullable=False) # a user maybe agent or User 

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
    ResolvedAt=db.Column(db.DateTime)
    Sla_due=db.Column(db.DateTime)
    Resolution=db.Column(db.String(500))
    ResolutionType=db.Column(db.String(20))
    

class TicketStats(db.Model):    
    id = db.Column(db.Integer, primary_key=True,auto_increment=True)
    tickets_today=db.Column(db.Integer)
    auto_resolved=db.Column(db.Integer)
    avg_resolution_time=db.Column(db.Integer)
    sla_breaches=db.Column(db.Integer)

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login',methods=['POST','GET'])
def login_page():
    if request.method=='POST':
        # we need to validate if the user is present in our DB, its password, role everything needs to be validated 
        useremail=request.form['useremail']
        password=request.form['password']
        user=User.query.filter_by(username=useremail).first()
        if user and user.password==password:
            #only if the user exists in the db and the passwords match only then are we allowing the user to enter the system
            session['useremail']=useremail
            session['role']=user.role
            return redirect('/welcome')
        else:
            return "Invalid Credentials"
    return render_template('login.html')

#creating landing page endpoint
@app.route('/welcome')
def welcome_page():
    return render_template('welcome.html')

@app.route('/welcome_agent')
def welcom_agent():
    #on the welcome page, we need to show stats to the agent (daily ticket stat)
    # for that we query the data from our tickets table and wrap it in the ticketStatus class which is then sent to the welcome_agent.html and rendered via jinja2template
    tickets_today=Ticket.query.filter(Ticket.CreatedAt>=date.today()).count()
    print(tickets_today)
    num_auto_resolved=Ticket.query.filter(Ticket.ResolutionType=="AUTO").count()
    avg_resolution_time = db.session.execute(
        db.select(
            func.avg(
                func.extract('epoch', Ticket.ResolvedAt - Ticket.CreatedAt) / 60
            )
        ).where(Ticket.ResolvedAt > date.today())
    ).scalar()
    avg_resolution_time = int(avg_resolution_time or 0)
    sla_breaches=Ticket.query.filter((Ticket.ResolvedAt>Ticket.Sla_due) | (Ticket.Sla_due<datetime.now())).count()
    ticketstats=TicketStats(tickets_today=tickets_today,auto_resolved=num_auto_resolved,avg_resolution_time=avg_resolution_time,sla_breaches=sla_breaches)
    # the significance of using .all() here is that The .all() method executes the database query and returns the results as a standard Python list containing your model objects (here Ticket object)
    # without all, it returns a pending query object which we cant loop through 
    return render_template('welcome_agent.html',TicketStats=ticketstats)

@app.route("/agent/tickets")
def fetch_all_tickets():
    tickets=Ticket.query.all()
    return render_template("fetch_all_tickets.html",Tickets=tickets)
@app.route("/resolve_ticket")
def resolve_ticket():
    ticket_id=request.args.get("id")
    return render_template("resolve_ticket.html",id=ticket_id)

@app.route('/raise_ticket',methods=['GET','POST'])
def raise_ticket():    
    if(request.method=='POST'):     
        shortDesc=request.form['shortDesc']
        longDesc=request.form['longDesc']
        issueType=request.form['issueType']
        priority=request.form['priority'] # all these fields shortDesc, longDesc are coming populated from the frontend 
        UserEmail=session['useremail'] # user email is taken from the current session only 
        if(priority=="P1"):
            sla_due=datetime.now() + timedelta(hours=4)
        elif(priority=="P2"):
            sla_due=datetime.now() +  timedelta(hours=8)
        else:
            sla_due=datetime.now() + timedelta(hours=12)
        ticket=Ticket(shortDesc=shortDesc,longDesc=longDesc,UserEmail=UserEmail,IssueType=issueType,Priority=priority,Status="OPEN",CreatedAt=datetime.now(),Sla_due=sla_due)
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
    print(app.url_map)
    app.run(debug=True,port=5001)
    