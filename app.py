from flask import Flask, render_template, request
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from openai import OpenAI
import logging
import re

app = Flask(__name__)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scrape_x_posts(username):
    posts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = f"https://x.com/{username}"
        page.goto(url, wait_until="networkidle", timeout=15000)
        
        page.on("response", lambda response: posts.extend(extract_posts(response)))
        
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(5000)
        
        if not posts:
            post_elements = page.query_selector_all('div[data-testid="tweetText"]')
            posts = [elem.inner_text() for elem in post_elements if elem.inner_text()]
                
        browser.close()
    return posts[:10]

def extract_posts(response):
    if "TweetResultByRestId" in response.url:
        try:
            data = response.json()
            tweet = data.get("data", {}).get("tweetResult", {}).get("result", {}).get("legacy", {})
            if "full_text" in tweet:
                return [tweet["full_text"]]
        except Exception:
            pass
    return []

def is_female_related(post):
    """Check if a post is related to women or directed toward them."""
    # Keywords related to women or female topics
    female_keywords = [
        r"\b(woman|women|girl|girls|female|ladies|lady|feminism|feminist|she|her|hers|wife|girlfriend|mom|mother|daughter|sister|aunt|grandma)\b",
        r"\b(gender|abortion|reproductive|sex\s*work|infidelity|promiscuity|cuck|cuckoldry|patriarchy|matriarchy|feminism|feminist|misogyny|misandry|equality|red\s*pill|mgtow|pay\s*gap)\b",
    ]
    # Check for @mentions (assume some might be female users)
    has_mention = bool(re.search(r"@\w+", post))
    
    # Match keywords (case-insensitive)
    for pattern in female_keywords:
        if re.search(pattern, post, re.IGNORECASE):
            return True
    # If it’s an @-mention with no keywords, assume it *might* be female-related (50/50 chance)
    return has_mention and len(post.split()) < 10  # Short posts with @ are more likely replies

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        username = request.form["username"].strip("@")
        try:
            post_texts = scrape_x_posts(username)
            if post_texts:
                # Filter for female-related posts
                female_posts = [post for post in post_texts if is_female_related(post)]
                if female_posts:
                    prompt = (
                        f"Analyze these posts from @{username} and rate how much of a 'simp' they are (0.0-10.0, 10.0 being extreme simp behavior like excessive flattery or pedestalization, 0.0 being absolute anti-feminist, e.g., MGTOW). "
                        "Use this point system loosely as a guide: +2 for unprompted flattery (e.g., 'you’re gorgeous' off-topic); +3 for glowing endorsements of women (e.g., praising capability excessively); +2 for excusing women’s accountability; +4 for supporting sex work, cuckoldry, promiscuity, or infidelity; +2 for degenerate PUA behavior (e.g., prioritizing meaningless sex as a life goal); -2 for rejecting women’s rights (e.g., voting); -1 for calling out bad behavior. "
                        "Cap at 10.0. Score starts at 0.0: 0-1 (anti-simp), 2-4 (mild simp traits), 5-7 (notable simp traits), 8-10 (high to extreme simp). "
                        "Explain briefly, showing point breakdown:\n\n" + "\n".join(female_posts)
                    )
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=150
                    )
                    analysis = response.choices[0].message.content
                    result = (
                        f"Posts for @{username} (female-related only):<br>" + "<br>".join(female_posts) +
                        f"<br><br>Simp Rating Analysis:<br>{analysis}"
                    )
                else:
                    result = f"No female-related posts found for @{username} in the sampled posts."
            else:
                result = f"No posts found for @{username}. Account may be private, invalid, or failed to load."
        except Exception as e:
            result = f"Error processing @{username}: {str(e)}"
            logger.error(f"Error: {str(e)}")
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host="0.0.0.0", port=10000)
