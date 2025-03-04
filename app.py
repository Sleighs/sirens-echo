from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        username = request.form["username"]
        result = f"Echoing {username}... (coming soon!)"  # Temporary placeholder
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)