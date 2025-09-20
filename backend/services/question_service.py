import os
import logging
from typing import List, Dict, Any
import json
import random
import hashlib
import asyncio
from datetime import datetime, timedelta

from models import Question, Difficulty, QuestionSet

logger = logging.getLogger(__name__)

class QuestionService:
    def __init__(self):
        # Initialize Gemini AI
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"QuestionService: GEMINI_API_KEY: {api_key}")
        if api_key:
            try:
                import google.generativeai as genai
                print(f"Gemini module imported: {dir(genai)[:10]}...")  # Show first 10 attributes
                genai.configure(api_key=api_key)
                
                # Store the genai module and set up the model
                self.genai = genai
                self.use_ai = True
                print("✅ Gemini AI configured successfully (using latest API)")
            except (ImportError, AttributeError) as e:
                print(f"❌ Failed to initialize Gemini AI: {e}")
                logger.warning(f"Failed to initialize Gemini AI: {e}. Using mock questions")
                self.use_ai = False
                self.genai = None
        else:
            self.use_ai = False
            self.genai = None
            logger.warning("GEMINI_API_KEY not found, using mock questions")
        
        # Cache for generated questions (topic -> QuestionSet)
        self.question_cache = {}
        self.cache_duration = timedelta(minutes=10)
    
    async def generate_questions(self, topic: str, count: int = 10) -> List[Question]:
        """Generate questions for a topic using Gemini API"""
        
        # Check cache first
        cache_key = f"{topic}_{count}"
        if cache_key in self.question_cache:
            cached_set = self.question_cache[cache_key]
            if datetime.utcnow() - cached_set.generated_at < self.cache_duration:
                print(f"Using cached questions for topic: {topic}")
                return cached_set.questions
        
        if not self.genai:
            logger.warning("Gemini API not available, using mock questions")
            return self._generate_mock_questions(topic, count)
        
        try:
            prompt = self._create_prompt(topic, count)
            # Use the new generate_content API
            model = self.genai.GenerativeModel('gemini-1.5-pro')
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 2048,
                    }
                )
            )
            
            # Parse the JSON response from the text content
            response_text = response.text.strip()
            # Sometimes the response might include markdown code blocks, so we need to extract the JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
                
            questions_data = json.loads(response_text)
            questions = []
            
            for i, q_data in enumerate(questions_data):
                question = Question(
                    id=f"{topic}_{i}_{hashlib.md5(q_data['prompt'].encode()).hexdigest()[:8]}",
                    prompt=q_data['prompt'],
                    options=q_data['options'],
                    correct_index=q_data['correctIndex'],
                    explanation=q_data['explanation'],
                    topic=topic,
                    difficulty=Difficulty(q_data.get('difficulty', 'medium'))
                )
                questions.append(question)
            
            # Cache the questions
            question_set = QuestionSet(topic=topic, questions=questions)
            self.question_cache[cache_key] = question_set
            
            print(f"Generated {len(questions)} questions for topic: {topic}")
            return questions
            
        except Exception as e:
            print(f"Error generating questions with Gemini: {e}")
            return self._generate_mock_questions(topic, count)
    
    def _create_prompt(self, topic: str, count: int) -> str:
        """Create prompt for Gemini API"""
        return f"""You are a quiz generator. Produce EXACTLY N={count} multiple-choice questions for the topic: "{topic}".
Output must be a JSON array of objects with fields:
- id (string short id),
- prompt (string),
- options (array of 4 concise strings),
- correctIndex (0..3),
- explanation (1-2 sentences),
- topic (echo),
- difficulty ("easy"|"medium"|"hard").

Constraints:
- Each question must be unambiguous and factually correct.
- Only one correct option per question.
- Avoid repeating subtopics; vary coverage.
- Keep prompts under 160 characters.
- Ensure options are mutually exclusive.
- Focus on practical programming knowledge and concepts.

Example format:
[
  {{
    "id": "q_01",
    "prompt": "Which sorting algorithm has average time complexity O(n log n)?",
    "options": ["Bubble Sort", "Merge Sort", "Insertion Sort", "Selection Sort"],
    "correctIndex": 1,
    "explanation": "Merge Sort divides and conquers to achieve O(n log n).",
    "topic": "{topic}",
    "difficulty": "medium"
  }}
]

Generate {count} questions now:"""
    
    def _generate_mock_questions(self, topic: str, count: int) -> List[Question]:
        """Generate mock questions for development/testing"""
        mock_questions = {
            "algorithms": [
                {
                    "prompt": "What is the time complexity of binary search?",
                    "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
                    "correct_index": 1,
                    "explanation": "Binary search divides the search space in half each time."
                },
                {
                    "prompt": "Which algorithm is used for finding shortest paths?",
                    "options": ["DFS", "BFS", "Dijkstra", "Merge Sort"],
                    "correct_index": 2,
                    "explanation": "Dijkstra's algorithm finds shortest paths in weighted graphs."
                }
            ],
            "javascript": [
                {
                    "prompt": "What does 'typeof null' return in JavaScript?",
                    "options": ["null", "undefined", "object", "boolean"],
                    "correct_index": 2,
                    "explanation": "This is a known quirk in JavaScript where typeof null returns 'object'."
                },
                {
                    "prompt": "Which method adds elements to the end of an array?",
                    "options": ["push()", "pop()", "shift()", "unshift()"],
                    "correct_index": 0,
                    "explanation": "push() adds elements to the end of an array."
                }
            ]
        }
        
        # Get base questions for topic or use algorithms as default
        base_questions = mock_questions.get(topic, mock_questions["algorithms"])
        
        questions = []
        for i in range(count):
            base_q = base_questions[i % len(base_questions)]
            question = Question(
                id=f"mock_{topic}_{i}",
                prompt=base_q["prompt"],
                options=base_q["options"],
                correct_index=base_q["correct_index"],
                explanation=base_q["explanation"],
                topic=topic,
                difficulty=Difficulty.MEDIUM
            )
            questions.append(question)
        
        return questions
    
    def clear_cache(self):
        """Clear the question cache"""
        self.question_cache.clear()
        print("Question cache cleared")
