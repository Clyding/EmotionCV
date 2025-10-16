import json
import random
import openai
import os

# Configuration - Set your API keys in environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')

class MLPipeline:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        
        # Emotion labels (7 classes as per your project)
        self.EMOTION_LABELS = ['anger', 'fear', 'disgust', 'happy', 'neutral', 'sad', 'surprise']
    
    def analyze_facial_emotions(self, facial_data):
        """
        Analyze facial emotions from webcam data
        In a real implementation, this would use your TensorFlow model
        """
        # Mock implementation - replace with actual model inference
        if facial_data and 'features' in facial_data:
            # Simulate model processing
            scores = {emotion: random.uniform(0, 1) for emotion in self.EMOTION_LABELS}
            # Normalize to sum to 1
            total = sum(scores.values())
            return {k: v/total for k, v in scores.items()}
        else:
            # Return neutral as default
            return {emotion: 0.0 for emotion in self.EMOTION_LABELS}
    
    def analyze_voice_emotions(self, voice_data):
        """
        Analyze voice emotions from audio data
        In a real implementation, this would use your RAVDESS-trained model
        """
        # Mock implementation - replace with actual model inference
        if voice_data and 'audio_features' in voice_data:
            scores = {emotion: random.uniform(0, 1) for emotion in self.EMOTION_LABELS}
            total = sum(scores.values())
            return {k: v/total for k, v in scores.items()}
        else:
            return {emotion: 0.0 for emotion in self.EMOTION_LABELS}
    
    def analyze_text_sentiment(self, text_input):
        """
        Analyze text sentiment and emotions
        """
        if not text_input:
            return {emotion: 0.0 for emotion in self.EMOTION_LABELS}
        
        # Simple keyword-based analysis (replace with proper NLP model)
        positive_words = ['happy', 'good', 'great', 'excellent', 'wonderful', 'amazing']
        negative_words = ['sad', 'bad', 'terrible', 'awful', 'horrible', 'angry']
        fear_words = ['scared', 'afraid', 'fear', 'worried', 'anxious']
        
        text_lower = text_input.lower()
        
        # Calculate scores based on keyword presence
        scores = {emotion: 0.0 for emotion in self.EMOTION_LABELS}
        
        if any(word in text_lower for word in positive_words):
            scores['happy'] = 0.7
            scores['neutral'] = 0.3
        
        if any(word in text_lower for word in negative_words):
            scores['sad'] = 0.5
            scores['anger'] = 0.3
            scores['disgust'] = 0.2
        
        if any(word in text_lower for word in fear_words):
            scores['fear'] = 0.8
            scores['surprise'] = 0.2
        
        # If no specific emotions detected, default to neutral
        if sum(scores.values()) == 0:
            scores['neutral'] = 1.0
        
        return scores
    
    def fuse_emotions(self, facial_scores, voice_scores, text_scores):
        """
        Fuse emotion scores from different modalities using weighted average
        """
        # Weights for different modalities (adjust based on reliability)
        weights = {
            'facial': 0.4,
            'voice': 0.3,
            'text': 0.3
        }
        
        fused_scores = {}
        for emotion in self.EMOTION_LABELS:
            fused_score = (
                facial_scores.get(emotion, 0) * weights['facial'] +
                voice_scores.get(emotion, 0) * weights['voice'] +
                text_scores.get(emotion, 0) * weights['text']
            )
            fused_scores[emotion] = round(fused_score, 3)
        
        return fused_scores
    
    def generate_ai_response(self, text_input, emotion_scores):
        """
        Generate empathetic AI response using GPT-4o
        """
        if not self.openai_client:
            return self._get_fallback_response(emotion_scores)
        
        try:
            # Format emotion information for prompt
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            emotion_summary = ", ".join([
                f"{emotion}: {score:.1%}" 
                for emotion, score in emotion_scores.items() 
                if score > 0.1
            ])
            
            prompt = f"""
            You are EmotionCV, an AI mental health support assistant. 
            User's emotional state: {emotion_summary}
            Dominant emotion: {dominant_emotion[0]} ({dominant_emotion[1]:.1%})
            
            User's message: "{text_input}"
            
            Provide a supportive, empathetic, and non-judgmental response. 
            Be concise but meaningful. Offer comfort and validation.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # or "gpt-4o" when available
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a compassionate mental health support assistant. Provide empathetic, supportive responses while being professional and caring. Keep responses under 100 words."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._get_fallback_response(emotion_scores)
    
    def assess_risk(self, text_input, emotion_scores):
        """
        Assess risk of self-harm or severe psychological distress
        """
        # Simple risk assessment (enhance with more sophisticated analysis)
        risk_factors = {
            'self_harm_keywords': ['kill myself', 'end it all', 'suicide', 'self harm', 'hurt myself'],
            'distress_keywords': ['cant take it', 'overwhelmed', 'hopeless', 'helpless', 'no point'],
            'high_risk_emotions': ['sad', 'anger', 'fear']
        }
        
        text_lower = text_input.lower()
        
        self_harm_risk = 0.0
        severe_stress_risk = 0.0
        
        # Check for self-harm keywords
        if any(keyword in text_lower for keyword in risk_factors['self_harm_keywords']):
            self_harm_risk = 0.9
        
        # Check for distress keywords
        if any(keyword in text_lower for keyword in risk_factors['distress_keywords']):
            severe_stress_risk = 0.7
        
        # Consider emotional state
        high_risk_emotion_score = sum(
            emotion_scores.get(emotion, 0) 
            for emotion in risk_factors['high_risk_emotions']
        )
        
        severe_stress_risk = max(severe_stress_risk, high_risk_emotion_score * 0.8)
        
        return {
            'self_harm_risk': round(self_harm_risk, 3),
            'severe_stress_risk': round(severe_stress_risk, 3),
            'triggers_found': len([k for k in risk_factors['self_harm_keywords'] if k in text_lower]),
            'assessment': 'High risk detected' if self_harm_risk > 0.5 else 'Moderate risk' if severe_stress_risk > 0.3 else 'Low risk'
        }
    
    def _get_fallback_response(self, emotion_scores):
        """Fallback response when AI service is unavailable"""
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        responses = {
            'happy': "I'm glad to see you're feeling positive! Remember to cherish these good moments.",
            'sad': "I'm here with you during this difficult time. Your feelings are valid and important.",
            'anger': "It's okay to feel angry. Would you like to talk about what's bothering you?",
            'fear': "I sense you're feeling anxious. Remember, you're stronger than you think.",
            'surprise': "Life can be full of surprises. I'm here to help you process whatever comes up.",
            'disgust': "I understand you're feeling upset. Let's work through this together.",
            'neutral': "I'm here to listen whenever you're ready to share. How are you really feeling?"
        }
        
        return responses.get(dominant_emotion[0], "I'm here to listen and support you. How can I help you today?")

# Global instance
ml_pipeline = MLPipeline()

# Public functions
def analyze_emotions(text_input="", voice_data=None, facial_data=None):
    """Main function to analyze emotions from all modalities"""
    facial_scores = ml_pipeline.analyze_facial_emotions(facial_data or {})
    voice_scores = ml_pipeline.analyze_voice_emotions(voice_data or {})
    text_scores = ml_pipeline.analyze_text_sentiment(text_input)
    
    fused_scores = ml_pipeline.fuse_emotions(facial_scores, voice_scores, text_scores)
    
    return fused_scores

def generate_ai_response(text_input, emotion_scores):
    """Generate AI response based on text and emotions"""
    return ml_pipeline.generate_ai_response(text_input, emotion_scores)

def assess_risk(text_input, emotion_scores):
    """Assess risk level"""
    return ml_pipeline.assess_risk(text_input, emotion_scores)
