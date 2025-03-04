from flask import Flask, render_template, request
import tweepy
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Twitter API setup
auth = tweepy.OAuthHandler(os.getenv("X_API_KEY"), os.getenv("X_API_SECRET"))
auth.set_access_token(os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_SECRET"))
api = tweepy.API(auth, wait_on_rate_limit=True)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        username = request.form["username"].strip("@")  # Remove @ if user includes it
        try:
            # Fetch user's recent tweets (max 10 for now)
            tweets = api.user_timeline(screen_name=username, count=10, tweet_mode="extended")
            tweet_texts = [tweet.full_text for tweet in tweets]
            if tweet_texts:
                result = f"Found {len(tweet_texts)} posts for @{username}:<br>" + "<br>".join(tweet_texts)
            else:
                result = f"No posts found for @{username}."
        except tweepy.TweepError as e:
            result = f"Error fetching posts for @{username}: {str(e)}"
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)