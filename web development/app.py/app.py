from flask  import Flask, render_template, redirect, url_for, request

# creating a instance of class flask
app = Flask(__name__)

# "/" stands for home direcotry
@app.route("/")
def home():
    #rednering index.html file
    return render_template("index.html")

#login page methods allowed psot and get
@app.route("/login", methods=["POST", "GET"])
def login():
    # request lib handles all the request of our web page
    # if mehtod of event is post send user to his local page
    if request.method == "POST":
        # form is a dicnaroy and we are retriveing user name from key 'nm' decleared in html form tag
        user = request.form["nm"]
        #after submit we are redirectoring user to his page and passing user as attribute
        return redirect(url_for("user", usr=user))
    else:
        # if no submit evnet is generated send user to login page and ask user to login
        return render_template("login.html")

# <usr> is used to send variable to our method
@app.route("/<usr>")
def user(usr):
    # we are rending a inline html to show user name
    return f"<h1>{usr}</h1>"

#entry point of our web page
if __name__ == "__main__":
    app.run()