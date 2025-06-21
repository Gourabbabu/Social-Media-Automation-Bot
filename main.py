from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import requests
from langchain_community.llms import LlamaCpp
import re
from datetime import datetime

app = FastAPI(title="Tweet Generator Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database configuration
DB_CONFIG = {
    "host": "db.ppexziazmxigonkmbied.supabase.co",
    "database": "postgres",
    "user": "postgres",
    "password": "nsRgB9jEpDEopEWX",
    "port": 5432,
    "sslmode": "require"
}

# Twitter API configuration
TWITTER_API_KEY = "gourab_078a9011a1db94660536008cdcfb6583"
TWITTER_POST_ENDPOINT = "https://twitterclone-server-2xz2.onrender.com/post_tweet"

# Initialize LLM
llm = None

def init_llm():
    global llm
    try:
        model_path = r"C:\Users\gourab\Desktop\tweet-generator-agent\mistral-7b-instruct-v0.2.Q6_K.gguf"
        llm = LlamaCpp(
            model_path=model_path,
            temperature=0.8,  # Increased for more creativity
            max_tokens=300,    # Increased to ensure completions
            top_p=0.95,
            verbose=False,
            n_ctx=2048
        )
        print("LLM initialized successfully")
    except Exception as e:
        print(f"Error initializing LLM: {e}")

# Pydantic models
class TweetGenerateRequest(BaseModel):
    topic: str
    tone: Optional[str] = "casual"
    include_hashtags: Optional[bool] = True
    target_audience: Optional[str] = "general"

class TweetEditRequest(BaseModel):
    tweet_id: int
    content: str

class TweetResponse(BaseModel):
    id: int
    content: str
    topic: str
    tone: str
    created_at: str
    status: str

# Database functions
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def create_tweets_table():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweets (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    topic VARCHAR(255) NOT NULL,
                    tone VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'draft'
                )
            """)
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table creation failed: {str(e)}")
    finally:
        conn.close()

# RAG-enhanced tweet generation system
class TweetKnowledgeBase:
    def __init__(self):
        # Curated examples covering various topics and tones
        self.examples = [
            {"topic": "AI progress", "tone": "excited", 
             "tweet": "Just saw the latest AI demo - mind blown! 🤯 The future is arriving faster than we expected. #AI #TechFuture #Innovation"},
            
            {"topic": "morning coffee", "tone": "casual", 
             "tweet": "That first sip of coffee in the morning - pure magic! ☕️ #CoffeeLover #MorningRitual #SimplePleasures"},
            
            {"topic": "weekend vibes", "tone": "happy", 
             "tweet": "Weekend mode: activated! Time for some R&R. What's everyone up to? 😎 #WeekendVibes #Relaxation"},
            
            {"topic": "tech news", "tone": "informative", 
             "tweet": "New smartphone launch has me tempted... but my wallet says no! 😅 Anyone else feeling this? #TechNews #GadgetLover"},
            
            {"topic": "fitness goals", "tone": "motivational", 
             "tweet": "Crushed my workout today! 💪 Remember: progress > perfection. #FitnessJourney #HealthFirst #Motivation"},
            
            {"topic": "climate change", "tone": "serious", 
             "tweet": "Just read the latest climate report. We need collective action NOW. Our planet depends on it. 🌍 #ClimateAction #Sustainability"},
            
            {"topic": "new project", "tone": "professional", 
             "tweet": "Thrilled to announce our new project launch! Can't wait to share more details soon. #NewBeginnings #TechInnovation"}
        ]
    
    def get_relevant_examples(self, topic: str, tone: str, count: int = 3) -> list:
        """Retrieve relevant tweet examples based on topic and tone similarity"""
        # Simple keyword matching - could be enhanced with embeddings
        topic_keywords = set(word.lower() for word in re.split(r'\W+', topic) if word)
        tone = tone.lower()
        
        # Score examples based on keyword matches and tone
        scored_examples = []
        for ex in self.examples:
            score = 0
            ex_keywords = set(word.lower() for word in re.split(r'\W+', ex["topic"]) if word)
            
            # Topic match scoring
            score += len(topic_keywords & ex_keywords) * 2
            
            # Tone match scoring
            if tone in ex["tone"].lower():
                score += 3
            elif tone in ex["tweet"].lower():
                score += 1
                
            scored_examples.append((score, ex))
        
        # Sort by score and return top examples
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored_examples[:count]]

# Initialize knowledge base
knowledge_base = TweetKnowledgeBase()

# Enhanced tweet generation with RAG
def generate_tweet_content(topic: str, tone: str, include_hashtags: bool, target_audience: str) -> str:
    if not llm:
        raise HTTPException(status_code=500, detail="AI model not initialized")
    
    # Get relevant examples from knowledge base
    examples = knowledge_base.get_relevant_examples(topic, tone)
    example_text = "\n".join(
        [f"Example ({ex['tone']} tone): {ex['tweet']}" for ex in examples]
    ) if examples else "No relevant examples found"
    
    # Hashtag instructions
    hashtag_instruction = ("Include 1-3 relevant hashtags at the end. " 
                           "Make sure hashtags are directly related to the content." 
                           if include_hashtags else "Do not include any hashtags.")
    
    # Enhanced prompt with RAG examples and constraints
    prompt = f"""
    You are an expert social media content creator. Your task is to generate a {tone}-style tweet about '{topic}' for {target_audience} audience.
    
    Guidelines:
    1. Create a COMPLETE, self-contained tweet (do not trail off with ellipses)
    2. Length: 240-280 characters (leaves room for engagement)
    3. {hashtag_instruction}
    4. Use 1-2 relevant emojis
    5. Make it engaging, authentic and appropriate for the target audience
    6. Structure: Clear beginning, middle, and end
    7. Ensure proper grammar and punctuation
    
    Relevant examples:
    {example_text}
    
    Now create a new tweet about: {topic}
    Tone: {tone}
    Target audience: {target_audience}
    
    Format your response as:
    [Your complete tweet text here]
    
    Important: Your response should ONLY contain the tweet content, nothing else.
    """
    
    try:
        # Generate with enhanced settings
        response = llm.invoke(
            prompt,
            stop=["\n\n", "Example:", "###", "<|endoftext|>"],  # Prevent copying examples
            max_tokens=300,
        )
        
        # Extract the tweet from the response
        tweet = response.strip()
        
        # Clean up common artifacts
        if tweet.startswith('"') and tweet.endswith('"'):
            tweet = tweet[1:-1]
        tweet = tweet.replace('\n', ' ').strip()
        
        # Ensure proper punctuation
        if tweet and tweet[-1] not in {'.', '!', '?', '…'}:
            tweet += '.'
            
        # Ensure hashtags are included if requested
        if include_hashtags and '#' not in tweet:
            # Add a fallback hashtag based on topic
            main_hashtag = '#' + re.sub(r'\W+', '', topic.title().replace(' ', ''))
            tweet += f" {main_hashtag}"
        
        # Final length adjustment
        if len(tweet) > 280:
            # Smart truncation at last sentence boundary
            last_punct = max(tweet.rfind('.'), tweet.rfind('!'), tweet.rfind('?'))
            if last_punct > 200 and last_punct < 280:
                tweet = tweet[:last_punct + 1]
            else:
                # Fallback truncation while preserving hashtags
                if '#' in tweet:
                    hashtag_part = tweet[tweet.rfind('#'):]
                    text_part = tweet[:tweet.rfind('#')].strip()
                    if len(text_part) > 240:
                        text_part = text_part[:237] + '...'
                    tweet = text_part + ' ' + hashtag_part
                else:
                    tweet = tweet[:277] + '...'
                    
        # Final validation
        if len(tweet) < 15:
            raise ValueError("Generated tweet is too short")
        if not any(char.isalnum() for char in tweet):
            raise ValueError("Generated tweet is empty")
            
        return tweet
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tweet generation failed: {str(e)}")

# API endpoints
@app.on_event("startup")
async def startup_event():
    init_llm()
    create_tweets_table()

@app.get("/")
async def root():
    return {"message": "Tweet Generator Agent API", "status": "running"}

@app.post("/generate-tweet", response_model=TweetResponse)
async def generate_tweet(request: TweetGenerateRequest):
    try:
        # Generate tweet content using AI
        content = generate_tweet_content(
            request.topic, 
            request.tone, 
            request.include_hashtags, 
            request.target_audience
        )
        
        # Save to database
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO tweets (content, topic, tone, status)
                    VALUES (%s, %s, %s, 'draft')
                    RETURNING id, content, topic, tone, created_at, status
                """, (content, request.topic, request.tone))
                
                tweet = cursor.fetchone()
                conn.commit()
                
                return TweetResponse(
                    id=tweet['id'],
                    content=tweet['content'],
                    topic=tweet['topic'],
                    tone=tweet['tone'],
                    created_at=str(tweet['created_at']),
                    status=tweet['status']
                )
        finally:
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tweet generation failed: {str(e)}")

@app.put("/edit-tweet/{tweet_id}", response_model=TweetResponse)
async def edit_tweet(tweet_id: int, request: TweetEditRequest):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                UPDATE tweets 
                SET content = %s 
                WHERE id = %s AND status = 'draft'
                RETURNING id, content, topic, tone, created_at, status
            """, (request.content, tweet_id))
            
            tweet = cursor.fetchone()
            if not tweet:
                raise HTTPException(status_code=404, detail="Tweet not found or already posted")
            
            conn.commit()
            
            return TweetResponse(
                id=tweet['id'],
                content=tweet['content'],
                topic=tweet['topic'],
                tone=tweet['tone'],
                created_at=str(tweet['created_at']),
                status=tweet['status']
            )
    finally:
        conn.close()

@app.post("/post-tweet/{tweet_id}")
async def post_tweet(tweet_id: int):
    conn = get_db_connection()
    try:
        # Get tweet from database
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM tweets 
                WHERE id = %s AND status = 'draft'
            """, (tweet_id,))
            
            tweet = cursor.fetchone()
            if not tweet:
                raise HTTPException(status_code=404, detail="Tweet not found or already posted")
            
            # Post to Twitter API
            headers = {
                "api-key": TWITTER_API_KEY,
                "Content-Type": "application/json"
            }
            
            payload = {
                "username": "gourab",
                "text": tweet['content']
            }
            
            response = requests.post(TWITTER_POST_ENDPOINT, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Update status to posted
                cursor.execute("""
                    UPDATE tweets 
                    SET status = 'posted' 
                    WHERE id = %s
                """, (tweet_id,))
                conn.commit()
                
                return {"message": "Tweet posted successfully", "tweet_id": tweet_id}
            else:
                raise HTTPException(status_code=400, detail=f"Failed to post tweet: {response.text}")
                
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Posting failed: {str(e)}")
    finally:
        conn.close()

@app.get("/tweets", response_model=List[TweetResponse])
async def get_tweets():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, content, topic, tone, created_at, status 
                FROM tweets 
                ORDER BY created_at DESC
            """)
            
            tweets = cursor.fetchall()
            
            return [
                TweetResponse(
                    id=tweet['id'],
                    content=tweet['content'],
                    topic=tweet['topic'],
                    tone=tweet['tone'],
                    created_at=str(tweet['created_at']),
                    status=tweet['status']
                )
                for tweet in tweets
            ]
    finally:
        conn.close()

@app.delete("/tweets/{tweet_id}")
async def delete_tweet(tweet_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM tweets WHERE id = %s", (tweet_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Tweet not found")
                
            return {"message": "Tweet deleted successfully"}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)