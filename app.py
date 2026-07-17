from flask import Flask,render_template,request,session,redirect,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,or_
from datetime import datetime
from datetime import date,timedelta
from langchain_core.documents import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
vectorizer=TfidfVectorizer(stop_words="english",ngram_range=(1,2))
historical_tickets = [
    {
        "id": "TKT-101",
        "description": "The VPN is not connecting. I keep getting error code 691 after entering my password.",
        "resolution": "Reset the user's VPN password in the Active Directory portal.",
    },{
        "id": "TKT-102",
        "description": "My outlook keeps crashing every time I try to open a shared mailbox. Help!",
        "resolution": "Run outlook.exe /safe to isolate the issue. Disable third-party add-ins.",
    },
    {
        "id": "TKT-103",
        "description": "Wi-Fi in the conference room is dropping packets and disconnecting.",
        "resolution": "Reboot the Cisco access point in Corridor B.",
    },
]
ticket_descriptions=[t["description"] for t in historical_tickets]
historical_keywords=vectorizer.fit_transform(ticket_descriptions)


def find_relevant_tickets(new_ticket_descirption,top_n=2):
    #we basically are accepting a new ticket from the user and passing it to this function 
    # This function uses TF IDF to a keyword frequency vector 
    new_keyword_vector=vectorizer.transform([new_ticket_descirption])
    #Now we compute the similarity of this vector with the already present tickets 
    
    key_word_score=cosine_similarity(new_keyword_vector,historical_keywords)[0]
    print(key_word_score)
    top_indices=np.argsort(key_word_score)[::-1][:top_n]
    results=[]
    for idx in top_indices:
        score=key_word_score[idx]
        if score>0:
            results.append({
                "shortDesc":historical_tickets[idx]["description"],
                "resolution":historical_tickets[idx]["resolution"]
            })
    return results

print(find_relevant_tickets("My outlook keeps crashing while trying to open a shared mailbox"))

app=Flask(__name__)
app.secret_key="jiya@123" # used to cryptographically sign the user session key 
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///itsm_ticket_resolution'
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
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    tickets_today=db.Column(db.Integer)
    auto_resolved=db.Column(db.Integer)
    avg_resolution_time=db.Column(db.Integer)
    sla_breaches=db.Column(db.Integer)

@app.route('/')
def hello_world():
    return 'Hello World!'

# creating a Jinja filter
@app.template_filter('timeago')
def timeago(value):
    diff=datetime.now()-value
    seconds=int(diff.total_seconds())
    if seconds<60:
        return f"{seconds} seconds ago"
    elif seconds<3600:
        return f"{seconds//60} minutes ago"
    elif seconds<86400:
        return f"{seconds//3600} hours ago"
    else:
        return f"{diff.days} days ago"

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
            if(user.role=="AGENT"):
                return redirect('/welcome_agent')
            else:
                return redirect('/welcome_user')
        else:
            return "Invalid Credentials"
    return render_template('login.html')

#creating landing page endpoint
@app.route('/welcome_user')
def welcome_user():
    open_requests = Ticket.query.filter_by(Status="OPEN").count()
    resolved_requests = Ticket.query.filter(Ticket.ResolvedAt.isnot(None)).count()
    return render_template('welcome.html', open_requests=open_requests, resolved_requests=resolved_requests)

@app.route('/welcome_agent')
def welcome_agent():
    #on the welcome page, we need to show stats to the agent (daily ticket stat)
    # for that we query the data from our tickets table and wrap it in the ticketStatus class which is then sent to the welcome_agent.html and rendered via jinja2template
    tickets_today=Ticket.query.filter(Ticket.CreatedAt>=date.today()).count()
    print(tickets_today)
    num_auto_resolved=Ticket.query.filter(Ticket.ResolutionType=="AUTO").count()
    #Fetching only the timestamps for resolved tickets
    tickets = db.session.query(Ticket.CreatedAt, Ticket.ResolvedAt).filter(
        Ticket.ResolvedAt.isnot(None),Ticket.CreatedAt>=func.current_date()
    ).all()
    #Using a simple Python loop to find the total differences in minutes
    if tickets:
        total_minutes = sum((t.ResolvedAt - t.CreatedAt).total_seconds() / 60 for t in tickets)
        avg_minutes = total_minutes / len(tickets)
        print(f"Average resolution time: {avg_minutes:.2f} minutes")
    else:
        avg_minutes = 0
    print(avg_minutes)   
   
    sla_breaches=Ticket.query.filter((Ticket.ResolvedAt>Ticket.Sla_due) | (Ticket.Sla_due<datetime.now())).count()
    ticketstats=TicketStats(tickets_today=tickets_today,auto_resolved=num_auto_resolved,avg_resolution_time=avg_minutes,sla_breaches=sla_breaches)
    # the significance of using .all() here is that The .all() method executes the database query and returns the results as a standard Python list containing your model objects (here Ticket object)
    # without all, it returns a pending query object which we cant loop through 
    tickets=Ticket.query.all()
    return render_template('welcome_agent.html',TicketStats=ticketstats,Tickets=tickets)
    

@app.route("/agent/tickets")
def fetch_all_tickets():
    tickets=Ticket.query.all()
    return render_template("fetch_all_tickets.html",Tickets=tickets)

@app.route("/resolve_ticket",methods=['GET','POST'])
def resolve_ticket():
    ticket_id=request.args.get('id',type=int)
    print(ticket_id)
    if request.method=='POST':
        resolution=request.form['resolution']        
        #now we need to save this resolution in our db
        print(ticket_id)
        ticket=Ticket.query.filter_by(TicketNumber=ticket_id).first()
        if ticket==None:
            print("Ticket not found")
        ticket.Resolution=resolution
        db.session.commit()
        return redirect('/agent/tickets')
    ticket=Ticket.query.filter_by(TicketNumber=ticket_id).first()
    print(ticket)
    return render_template("resolve_ticket.html",Ticket=ticket)


@app.route("/close_ticket/<ticket_id>",methods=['POST'])
def close_ticket(ticket_id):    
    print(ticket_id)
    ticket=Ticket.query.filter_by(TicketNumber=ticket_id).first()
    ticket.Status="CLOSED"
    ticket.ResolvedAt=datetime.now() # we set the resolution time of the ticket to now 
    db.session.commit()
    #once a ticket is closed we store its resolution along with the short Desc in out vector store to answer future queries 
    langChainDoc=Document(page_content=f"Problem: {ticket.shortDesc}+Resolution:{ticket.Resolution}")# for now keepign the metadata empty but it can make us trade off a lot of filtering options
    save_to_qdrant(langChainDoc)
    print("Ticket successfully closed")
    return {"success": True}, 200

@app.route('/raise_ticket',methods=['GET','POST'])
def raise_ticket():    
    if(request.method=='POST'):     
        # here after posting the ticket, the user should see a resolution
        shortDesc=request.form['shortDesc']
        longDesc=request.form['longDesc']
        issueType=request.form['issueType']
        priority=request.form['priority'] # all these fields shortDesc, longDesc are coming populated from the frontend 
        UserEmail=session['useremail'] # user email is taken from the current session only 
        suggestions=find_relevant_tickets(shortDesc)      
        
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


@app.route('/accept_resolution')
def accept_rag_resolution():
    ticket_number=request.args.get("ticket_number")
    ticket=Ticket.query.filter_by(Ticket.TicketNumber==ticket_number).first()
    # we now need to set the resolution provided by rag in the DB to be later rendered to the user

@app.route('/my_tickets')
def fetch_my_tickets():
    # we now need to query the database to fetch tickets with the required user email id 
    email=session['useremail']
    tickets=Ticket.query.filter_by(UserEmail=email).all()
    return render_template("my_tickets.html",tickets=tickets)#we are sending the filtered tickets to the frontend via the render_template method 


@app.route('/suggest_resolutions',methods=['POST'])
def suggest_resolutions():
    #this will be receiving data in JSON format
    data=request.get_json()
    new_ticket_description=data.get('description','')
    suggestions=find_relevant_tickets(new_ticket_description)
    print(suggestions)
    return jsonify(suggestions)

with app.app_context():
    db.create_all()

    default_user = User.query.filter_by(username="jiyakapoor1409@gmil.com").first()
    if default_user is None:
        db.session.add(User(username="jiyakapoor1409@gmil.com", password="jiya@123", role="USER"))
        db.session.commit()

    print("USer entry added")
    

if __name__=="__main__":    
    app.run(debug=True,port=5001)
