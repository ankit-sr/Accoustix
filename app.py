from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, send, emit, join_room
from flask_pymongo import PyMongo
from time import localtime, strftime
from passlib.hash import pbkdf2_sha256
from flask_mail import Message, Mail

current_user = "test"

app = Flask(__name__)

#  Contact Us:
file = open("credentials.txt", "r")
own_email = file.readline().strip()
own_password = file.readline().strip()
file.close()

mail = Mail(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = own_email
app.config["MAIL_PASSWORD"] = own_password
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)


# Database integration
app.config["MONGO_URI"] = "mongodb://localhost:27017/ChatSquad"
mongodb_client = PyMongo(app)
db = mongodb_client.db

app.config["SECRET_KEY"] = "melodyitnichocolatykyuhai"
# Creating an instance of SocketIO using constructor.
socketio = SocketIO(app)


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat")
def chat():
    return render_template("chat.html", username=current_user)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # getting user's data from registration page
        users = db.users
        first_name = request.form["first-name"]
        last_name = request.form["last-name"]
        email = request.form["email"]
        dob = request.form["user-dob"]
        username = request.form["username"]
        password = request.form["password"]

        existing_user = users.find_one({"email": email, "username": username})
        if existing_user is None:
            # encrypting user's password for protection.
            hashed_password = pbkdf2_sha256.hash(password)

            # inserting data into the db.
            users.insert_one(
                {
                    "email": email,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "dob": dob,
                    "password": hashed_password,
                }
            )

    return render_template("register.html")


@app.route("/contact", methods=["POST", "GET"])
def contact():
    messageSent = 0
    if request.method == "POST":
        usr_name = request.form["name"]
        usr_email = request.form["email"]
        usr_msg = request.form["message"]

        msg = Message(
            "Accoustix Contact Response",
            sender=own_email,
            recipients=[usr_email],
        )

        msg.body = f"""
        Hi {usr_name}👋,

        Thank you for contacting us.

        We've recieved your message and one of our team members will get back to you soon.

        Best Regards,
        Team Accoustix.
        """

        mail.send(msg)
        messageSent = 1

    return render_template("contact.html", messageSent=messageSent)


@app.route("/login", methods=["POST", "GET"])
def login():
    wrong_credentials = 0
    if request.method == "POST":
        users = db.users
        user_email = request.form["email"]
        user_password = request.form["password"]

        current_user = users.find_one({"email": user_email})
        print(current_user)

        if current_user and pbkdf2_sha256.verify(
            user_password, current_user["password"]
        ):
            return redirect(url_for("chat"))
        else:
            wrong_credentials = 1
            return render_template("login.html", wrong_credentials=wrong_credentials)

    return render_template("login.html")


@socketio.on("message")
def message(data):
    # print("Message: ", data, "\n\n\n\n")
    send(
        {
            "msg": data["msg"],
            "username": data["username"],
            "timestamp": strftime("%b-%d %I:%M%p", localtime()),
        }
    )


@socketio.on("join")
def join(data):
    join_room(data["room"])
    send({"msg": data["username"] + "has joined the room"})


if __name__ == "__main__":
    socketio.run(app, debug=True)
