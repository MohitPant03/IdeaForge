from groq import Groq
from flask import current_app
import json

def analyze_idea(title, description, category):
    try:
        client = Groq(api_key=current_app.config['GROQ_API_KEY'])
        
        prompt = f"""
        Analyze this startup/project idea and provide structured feedback.
        
        Title: {title}
        Category: {category}
        Description: {description}
        
        Respond ONLY in this exact JSON format, nothing else:
        {{
            "strengths": ["strength 1", "strength 2", "strength 3"],
            "weaknesses": ["weakness 1", "weakness 2"],
            "risks": ["risk 1", "risk 2"],
            "questions": ["question 1", "question 2"]
        }}
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.choices[0].message.content.strip()
        
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        
        result = json.loads(text)
        return result
        
    except Exception as e:
        print(f"AI Error: {e}")
        return {
            "strengths": ["Interesting concept worth exploring"],
            "weaknesses": ["Needs more detailed description"],
            "risks": ["Market validation required"],
            "questions": ["Who is your target audience?"]
        }