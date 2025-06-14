# 🤖 Social Media AutoPost Bot

A smart AI-powered chatbot that takes a simple text prompt, generates an engaging social media post, and automatically publishes it to your chosen platform (e.g., Twitter, LinkedIn, Instagram).

## ✨ Features

- 🧠 AI-generated captions from your input prompt
- 🖼️ Optional image generation using text-to-image models (like DALL·E or Stable Diffusion)
- 📅 Automatic posting to social platforms via API (e.g., Twitter/X API, LinkedIn API)
- 🏷️ Hashtag suggestions
- 🔄 Scheduled posting support *(optional)*

## 🚀 How It Works

1. You give a prompt like:
   ```
   "Promote my new AI project that creates songs from emotions"
   ```
2. The bot:
   - Generates a caption
   - Suggests or generates an image
   - Posts it to your social media account via API

## 🛠️ Tech Stack

- Python 🐍
- OpenAI GPT / LLMs for content generation
- PIL / DALL·E / SDXL for image generation *(optional)*
- Tweepy / LinkedIn API / Meta Graph API for posting
- dotenv for secret/API key management

## 📦 Installation

``` bash
git clone https://github.com/yourusername/social-media-autopost-bot.git
cd social-media-autopost-bot
pip install -r requirements.txt
```

Set your API keys in a \`.env\` file:

```env
OPENAI_API_KEY=your_openai_key
TWITTER_API_KEY=your_twitter_key
...
```

## 🧪 Example Usage

```bash
python bot.py "Launch announcement for my AI YouTube channel"
```

Output:
```
✅ Post generated and shared on Twitter:
"🚀 Just launched my new YouTube series on AI projects that turn emotions into code! Check it out now! #AI #YouTube #Innovation"
```

## 📌 To-Do

- [ ] Add image generation support
- [ ] Support multiple platforms
- [ ] Build a web interface (Gradio/Streamlit)
- [ ] Schedule posts with a cron job or UI

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.


