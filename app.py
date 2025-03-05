from flask import Flask, render_template, request
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from openai import OpenAI
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scrape_x_posts(username):
    posts = []
    with sync_playwright() as p:
        logger.debug("Launching headless Chromium browser")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = f"https://x.com/{username}"
        logger.debug(f"Navigating to {url}")
        response = page.goto(url, wait_until="networkidle", timeout=15000)  # 15s timeout
        logger.debug(f"Page loaded with status: {response.status}")
        
        # Log all responses to debug
        def log_response(response):
            logger.debug(f"Response URL: {response.url}")
            posts.extend(extract_posts(response))
        page.on("response", log_response)
        
        # Scroll and wait longer
        logger.debug("Scrolling to load additional posts")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(5000)  # 5 seconds to load more
        
        # Fallback: Parse HTML if no posts from requests
        if not posts:
            logger.debug("No posts from requests, trying HTML fallback")
            post_elements = page.query_selector_all('div[data-testid="tweetText"]')
            posts = [elem.inner_text() for elem in post_elements if elem.inner_text()]
            logger.debug(f"Collected {len(posts)} posts from HTML: {posts}")
                
        browser.close()
    return posts[:10]

def extract_posts(response):
    if "TweetResultByRestId" in response.url:
        try:
            data = response.json()
            tweet = data.get("data", {}).get("tweetResult", {}).get("result", {}).get("legacy", {})
            if "full_text" in tweet:
                logger.debug(f"Extracted post from API: {tweet['full_text']}")
                return [tweet['full_text']]
        except Exception:
            pass
    return []

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        username = request.form["username"].strip("@")
        logger.debug(f"Received POST request for @{username}")
        try:
            logger.debug("Starting post scrape")
            post_texts = scrape_x_posts(username)
            logger.debug(f"Scraped {len(post_texts)} posts: {post_texts}")
            if post_texts:
                logger.debug("Preparing OpenAI prompt")
                prompt = (
                    f"Analyze these posts from @{username} and rate how much of a 'simp' they are (0-10, 10 being extreme simp behavior like excessive flattery or pedestalization). "
                    "Use the 4 waves of feminism as a guide: 1st (suffrage)—support isn’t inherently simping, rejecting it is anti-simp; "
                    "2nd (workplace/reproductive)—backing CEOs or abortion leans simpish if unconditional; "
                    "3rd (intersectionality)—excusing accountability is simpish; "
                    "4th (sex positivity)—supporting sex work, cuckoldry, promiscuity, or infidelity is high simping. "
                    "Key indicators: unprompted flattery (e.g., 'you’re gorgeous' off-topic) is mid-to-high; "
                    "agreeing women aren’t accountable is simpish; backing infidelity or promiscuity is 8-10; "
                    "rejecting voting rights or calling out bad behavior is 0-1. "
                    "Score: 0-1 (rejects 1st wave), 2-4 (some 1st/2nd support), 5-7 (2nd/3rd support), 8-10 (3rd/4th, extreme pandering). "
                    "Explain briefly:\n\n" + "\n".join(post_texts)
                )
                logger.debug("Sending request to OpenAI")
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                analysis = response.choices[0].message.content
                logger.debug(f"OpenAI response: {analysis}")
                result = f"Posts for @{username}:<br>" + "<br>".join(post_texts) + f"<br><br>Simp Rating Analysis:<br>{analysis}"
            else:
                result = f"No posts found for @{username}. Account may be private, invalid, or failed to load."
                logger.debug(result)
        except Exception as e:
            result = f"Error processing @{username}: {str(e)}"
            logger.error(f"Error occurred: {str(e)}")
    logger.debug(f"Rendering template with result: {result}")
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)