from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home_page.html")

@app.route("/destinations")
def destinations():
    return render_template("destination.html")

if __name__ == "__main__":
    app.run(debug=True)
