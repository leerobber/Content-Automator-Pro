from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import anthropic
import os
import uuid
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment
API_KEY = os.environ.get("ANTHROPIC_KEY", "")
if API_KEY:
    client = anthropic.Anthropic(api_key=API_KEY)
else:
    client = None

# Simple user database
users = {
    "demo@test.com": {"password": "demo123", "credits": 10}
}

class ContentRequest(BaseModel):
    email: str
    password: str
    topic: str
    keywords: List[str]

class RatingRequest(BaseModel):
    email: str
    content_id: str
    rating: int

# In-memory ratings store
ratings = {}

@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AI Content Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            font-size: 1.8em;
            text-align: center;
            margin-bottom: 10px;
        }
        .price {
            text-align: center;
            font-size: 1.3em;
            color: #333;
            margin: 15px 0;
            font-weight: bold;
        }
        .feature {
            margin: 8px 0;
            color: #555;
            font-size: 0.95em;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 17px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 8px;
        }
        button:active { opacity: 0.8; }
        #result {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
            max-height: 350px;
            overflow-y: auto;
            font-size: 0.9em;
            line-height: 1.5;
        }
        .demo-box {
            background: #fef3c7;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
            font-size: 0.9em;
        }
        .status {
            text-align: center;
            padding: 8px;
            background: #d1fae5;
            color: #065f46;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 0.85em;
        }
        .rating-section {
            margin-top: 14px;
            text-align: center;
        }
        .rating-section p {
            margin-bottom: 8px;
            font-weight: bold;
            color: #444;
        }
        .rating-btn {
            width: auto;
            padding: 6px 10px;
            margin: 3px 2px;
            background: #e5e7eb;
            color: #333;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 15px;
            font-weight: normal;
            cursor: pointer;
            display: inline-block;
        }
        .rating-btn:hover { background: #667eea; color: white; }
        .rating-btn.selected { background: #667eea; color: white; border-color: #667eea; }
        #rating-feedback {
            margin-top: 8px;
            font-size: 0.9em;
            color: #059669;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Content Generator</h1>
        <div class="price">$29/month</div>
        
        <div class="status">✅ System Online - Free Demo Active</div>
        
        <div class="feature">✅ Full articles in 30 seconds</div>
        <div class="feature">✅ SEO optimized content</div>
        <div class="feature">✅ Blog posts & social media</div>
        <div class="feature">✅ Save 10+ hours weekly</div>

        <div class="demo-box">
            <strong>🎉 Free Demo Active</strong><br>
            <small>Demo login: demo@test.com / demo123</small>
        </div>

        <input type="text" id="topic" placeholder="Enter topic (e.g., 'Best laptops 2025')" />
        <input type="text" id="keywords" placeholder="Keywords (e.g., laptops, review)" />
        <button onclick="generate()">✨ Generate AI Content</button>
        
        <div id="result"></div>
    </div>

    <script>
        let currentContentId = null;

        async function generate() {
            const topic = document.getElementById('topic').value;
            const keywords = document.getElementById('keywords').value.split(',').map(k => k.trim());
            const result = document.getElementById('result');
            
            if (!topic) {
                alert('Please enter a topic!');
                return;
            }
            
            currentContentId = null;
            result.style.display = 'block';
            result.innerHTML = '<div style="text-align:center">⏳ AI writing... (30 sec)</div>';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        email: 'demo@test.com',
                        password: 'demo123',
                        topic: topic,
                        keywords: keywords
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    currentContentId = data.content_id;
                    const ratingBtns = [1,2,3,4,5,6,7,8,9,10].map(n =>
                        `<button class="rating-btn" onclick="rateContent(${n}, this)">${n}</button>`
                    ).join('');
                    result.innerHTML = `
                        <h3 style="color: #059669; margin-bottom: 10px;">✅ Content Ready!</h3>
                        <div style="background: white; padding: 12px; border-radius: 5px; border: 1px solid #e5e7eb; white-space: pre-wrap; font-size: 0.85em;">
${data.content}
                        </div>
                        <p style="margin-top: 10px;"><strong>Credits:</strong> ${data.credits_remaining} left</p>
                        <p style="color: #059669; margin-top: 8px; font-weight: bold;">
                            💰 Upgrade for unlimited: $29/month
                        </p>
                        <div class="rating-section">
                            <p>Rate this content (1–10):</p>
                            ${ratingBtns}
                            <div id="rating-feedback"></div>
                        </div>
                    `;
                } else {
                    result.innerHTML = `<p style="color: #dc2626;">❌ ${data.detail}</p>`;
                }
            } catch (error) {
                result.innerHTML = `<p style="color: #dc2626;">❌ Connection error. Try again!</p>`;
            }
        }

        async function rateContent(rating, btn) {
            document.querySelectorAll('.rating-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            const feedback = document.getElementById('rating-feedback');
            feedback.textContent = 'Submitting...';
            try {
                const response = await fetch('/rate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        email: 'demo@test.com',
                        content_id: currentContentId,
                        rating: rating
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    feedback.textContent = `⭐ Thanks! You rated this ${rating}/10.`;
                } else {
                    feedback.textContent = `❌ ${data.detail}`;
                }
            } catch (error) {
                feedback.textContent = '❌ Could not submit rating.';
            }
        }
    </script>
</body>
</html>
    """

@app.post("/generate")
async def generate_content(request: ContentRequest):
    if not client:
        raise HTTPException(status_code=500, detail="API key not configured. Add ANTHROPIC_KEY environment variable.")
    
    user = users.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid login")
    
    if user["credits"] <= 0:
        raise HTTPException(status_code=402, detail="No credits! Upgrade for unlimited at $29/month")
    
    prompt = f"""Write a compelling 500-word article about: {request.topic}

Keywords to include: {', '.join(request.keywords)}

Structure:
- Engaging hook
- 3 key points
- Practical examples
- Strong conclusion

Professional but conversational tone."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        content_id = str(uuid.uuid4())
        users[request.email]["credits"] -= 1
        
        return {
            "content": content,
            "content_id": content_id,
            "credits_remaining": users[request.email]["credits"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

@app.post("/rate")
async def rate_content(request: RatingRequest):
    if request.rating < 1 or request.rating > 10:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 10")
    user = users.get(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    ratings[f"{request.content_id}:{request.email}"] = request.rating
    return {"message": "Rating saved", "content_id": request.content_id, "rating": request.rating}

@app.get("/health")
async def health():
    return {"status": "running", "app": "Content Automator Pro"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)