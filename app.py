from flask import Flask, render_template, request
import tweepy
from dotenv import load_dotenv
import os
from openai import OpenAI

app = Flask(__name__)

load_dotenv()

# X API setup
auth = tweepy.OAuthHandler(os.getenv("X_API_KEY"), os.getenv("X_API_SECRET"))
auth.set_access_token(os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_SECRET"))
api = tweepy.API(auth, wait_on_rate_limit=True)

# OpenAI setup
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        username = request.form["username"].strip("@")
        print(f"Attempting to fetch posts for @{username}")  # Debug log
        try:
            posts = api.user_timeline(screen_name=username, count=10, tweet_mode="extended")
            post_texts = [post.full_text for post in posts]
            print(f"Fetched {len(post_texts)} posts")  # Debug log
            if post_texts:
                prompt = f"Analyze these posts from @{username} and rate how much of a 'simp' they are (0-10, 10 being extreme simp behavior like excessive flattery). Explain briefly:\n\n" + "\n".join(post_texts)
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                analysis = response.choices[0].message.content
                result = f"Posts for @{username}:<br>" + "<br>".join(post_texts) + f"<br><br>Simp Rating Analysis:<br>{analysis}"
            else:
                result = f"No posts found for @{username}."
        except tweepy.NotFound:
            result = f"User @{username} not found on X."
        except tweepy.Forbidden as e:
            result = f"Cannot access @{username}'s posts (private or restricted). Details: {str(e)}"
        except tweepy.TweepyException as e:
            result = f"X API error for @{username}: {str(e)}"
        except Exception as e:
            result = f"General error for @{username}: {str(e)}"
        print(f"Result: {result}")  # Debug log
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)