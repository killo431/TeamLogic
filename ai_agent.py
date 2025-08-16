"""
AI Agent Module for Knowledge Base Framework
Integrates with local AI models for enhanced knowledge processing
"""

import logging
import json
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
from datetime import datetime
import re
import warnings

# Suppress warnings from transformers library
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from transformers import AutoTokenizer, AutoModel, pipeline, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIAgentError(Exception):
    """Custom exception for AI agent operations"""
    pass


class LocalAIModel:
    """Manages local AI models for various tasks"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased", device: str = "auto"):
        self.model_name = model_name
        self.device = self._determine_device(device)
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.logger = logging.getLogger(__name__)
        
        if not TRANSFORMERS_AVAILABLE:
            raise AIAgentError("Transformers library not available. Please install: pip install transformers torch")
            
    def _determine_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == "auto":
            if TRANSFORMERS_AVAILABLE:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            return "cpu"
        return device
        
    def load_model(self, task: str = "feature-extraction"):
        """Load the AI model for specific task"""
        try:
            self.logger.info(f"Loading model {self.model_name} for task: {task}")
            
            if task == "feature-extraction":
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                if self.device == "cuda":
                    self.model = self.model.cuda()
                    
            elif task in ["text-generation", "question-answering", "summarization"]:
                self.pipeline = pipeline(
                    task, 
                    model=self.model_name, 
                    device=0 if self.device == "cuda" else -1
                )
            else:
                # Generic pipeline
                self.pipeline = pipeline(
                    task, 
                    model=self.model_name,
                    device=0 if self.device == "cuda" else -1
                )
                
            self.logger.info(f"Successfully loaded model on {self.device}")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise AIAgentError(f"Failed to load model {self.model_name}: {e}")
            
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using the local model"""
        if not self.model or not self.tokenizer:
            self.load_model("feature-extraction")
            
        embeddings = []
        
        for text in texts:
            try:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                if self.device == "cuda":
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                    
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # Use mean pooling of the last hidden state
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
                    
                if self.device == "cuda":
                    embedding = embedding.cpu()
                    
                embeddings.append(embedding.numpy().tolist())
                
            except Exception as e:
                self.logger.error(f"Error generating embedding for text: {e}")
                embeddings.append([0.0] * 768)  # Default embedding size
                
        return embeddings
        
    def generate_text(self, prompt: str, max_length: int = 100, 
                     num_return_sequences: int = 1) -> List[str]:
        """Generate text using the local model"""
        if not self.pipeline or self.pipeline.task != "text-generation":
            # Try to load a text generation model
            try:
                self.model_name = "gpt2"  # Fallback to GPT-2
                self.load_model("text-generation")
            except:
                raise AIAgentError("Text generation model not available")
                
        try:
            outputs = self.pipeline(
                prompt,
                max_length=max_length,
                num_return_sequences=num_return_sequences,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.pipeline.tokenizer.eos_token_id
            )
            
            return [output['generated_text'] for output in outputs]
            
        except Exception as e:
            self.logger.error(f"Error in text generation: {e}")
            return [f"Error: {e}"]


class KnowledgeProcessor:
    """Processes knowledge using AI models"""
    
    def __init__(self, ai_model: LocalAIModel):
        self.ai_model = ai_model
        self.logger = logging.getLogger(__name__)
        
    def extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using NER"""
        try:
            # Load NER pipeline if not already loaded
            if not hasattr(self, 'ner_pipeline'):
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dbmdz/bert-large-cased-finetuned-conll03-english",
                    aggregation_strategy="simple",
                    device=0 if self.ai_model.device == "cuda" else -1
                )
                
            entities = self.ner_pipeline(text)
            
            # Convert to our entity format
            processed_entities = []
            for entity in entities:
                processed_entity = {
                    'text': entity['word'],
                    'label': entity['entity_group'],
                    'confidence': entity['score'],
                    'start': entity.get('start', 0),
                    'end': entity.get('end', 0)
                }
                processed_entities.append(processed_entity)
                
            return processed_entities
            
        except Exception as e:
            self.logger.error(f"Error in entity extraction: {e}")
            return []
            
    def summarize_text(self, text: str, max_length: int = 150, 
                      min_length: int = 30) -> str:
        """Summarize text using AI model"""
        try:
            # Load summarization pipeline if not already loaded
            if not hasattr(self, 'summarization_pipeline'):
                self.summarization_pipeline = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    device=0 if self.ai_model.device == "cuda" else -1
                )
                
            # Truncate text if too long
            max_input_length = 1024
            if len(text) > max_input_length:
                text = text[:max_input_length]
                
            summary = self.summarization_pipeline(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            return summary[0]['summary_text']
            
        except Exception as e:
            self.logger.error(f"Error in text summarization: {e}")
            return f"Summarization failed: {e}"
            
    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer question based on context using AI model"""
        try:
            # Load QA pipeline if not already loaded
            if not hasattr(self, 'qa_pipeline'):
                self.qa_pipeline = pipeline(
                    "question-answering",
                    model="distilbert-base-cased-distilled-squad",
                    device=0 if self.ai_model.device == "cuda" else -1
                )
                
            result = self.qa_pipeline(question=question, context=context)
            
            return {
                'answer': result['answer'],
                'confidence': result['score'],
                'start': result['start'],
                'end': result['end']
            }
            
        except Exception as e:
            self.logger.error(f"Error in question answering: {e}")
            return {
                'answer': f"Error: {e}",
                'confidence': 0.0,
                'start': 0,
                'end': 0
            }
            
    def classify_text(self, text: str, labels: List[str]) -> Dict[str, float]:
        """Classify text into given labels"""
        try:
            # Load zero-shot classification pipeline
            if not hasattr(self, 'classification_pipeline'):
                self.classification_pipeline = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if self.ai_model.device == "cuda" else -1
                )
                
            result = self.classification_pipeline(text, labels)
            
            # Convert to dict format
            classification = {}
            for label, score in zip(result['labels'], result['scores']):
                classification[label] = score
                
            return classification
            
        except Exception as e:
            self.logger.error(f"Error in text classification: {e}")
            return {label: 0.0 for label in labels}


class ConversationalAgent:
    """Conversational AI agent for knowledge interaction"""
    
    def __init__(self, ai_model: LocalAIModel, knowledge_processor: KnowledgeProcessor):
        self.ai_model = ai_model
        self.knowledge_processor = knowledge_processor
        self.conversation_history: List[Dict[str, str]] = []
        self.logger = logging.getLogger(__name__)
        
    def chat(self, message: str, context: Optional[str] = None) -> str:
        """Chat with the AI agent"""
        try:
            # Build conversation context
            conversation_context = self._build_context(context)
            
            # Create prompt
            prompt = self._create_prompt(message, conversation_context)
            
            # Generate response
            responses = self.ai_model.generate_text(prompt, max_length=200)
            response = responses[0] if responses else "I'm sorry, I couldn't generate a response."
            
            # Clean up response (remove prompt if included)
            if prompt in response:
                response = response.replace(prompt, "").strip()
                
            # Add to conversation history
            self.conversation_history.append({
                'user': message,
                'assistant': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 exchanges
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return f"I encountered an error: {e}"
            
    def _build_context(self, additional_context: Optional[str] = None) -> str:
        """Build conversation context from history"""
        context_parts = []
        
        # Add recent conversation history
        for exchange in self.conversation_history[-3:]:  # Last 3 exchanges
            context_parts.append(f"User: {exchange['user']}")
            context_parts.append(f"Assistant: {exchange['assistant']}")
            
        # Add additional context if provided
        if additional_context:
            context_parts.append(f"Context: {additional_context}")
            
        return "\n".join(context_parts)
        
    def _create_prompt(self, message: str, context: str) -> str:
        """Create AI prompt from message and context"""
        system_prompt = """You are a helpful AI assistant that helps users with their knowledge management tasks. 
You can answer questions, provide summaries, and help organize information. 
Be concise and helpful in your responses."""
        
        if context:
            prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser: {message}\nAssistant:"
        else:
            prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            
        return prompt
        
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
        
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()


class AIAgent:
    """Main AI Agent class that coordinates all AI functionalities"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased", device: str = "auto"):
        self.model_name = model_name
        self.device = device
        self.ai_model = None
        self.knowledge_processor = None
        self.conversational_agent = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize AI components"""
        try:
            self.ai_model = LocalAIModel(self.model_name, self.device)
            self.knowledge_processor = KnowledgeProcessor(self.ai_model)
            self.conversational_agent = ConversationalAgent(self.ai_model, self.knowledge_processor)
            
            self.logger.info("AI Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing AI Agent: {e}")
            raise AIAgentError(f"Failed to initialize AI Agent: {e}")
            
    def process_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process entities with AI enhancement"""
        processed_entities = []
        
        for entity in entities:
            try:
                # Extract text content from entity
                text_content = self._extract_text_from_entity(entity)
                
                if text_content:
                    # Extract additional entities from text
                    extracted_entities = self.knowledge_processor.extract_entities_from_text(text_content)
                    
                    # Add AI-extracted entities to entity attributes
                    if extracted_entities:
                        entity['ai_extracted_entities'] = extracted_entities
                        
                    # Generate summary if text is long
                    if len(text_content) > 500:
                        summary = self.knowledge_processor.summarize_text(text_content)
                        entity['ai_summary'] = summary
                        
                    # Classify entity content
                    labels = ['technical', 'business', 'personal', 'project', 'documentation']
                    classification = self.knowledge_processor.classify_text(text_content, labels)
                    entity['ai_classification'] = classification
                    
                processed_entities.append(entity)
                
            except Exception as e:
                self.logger.error(f"Error processing entity {entity.get('id', 'unknown')}: {e}")
                processed_entities.append(entity)  # Keep original entity
                
        return processed_entities
        
    def _extract_text_from_entity(self, entity: Dict[str, Any]) -> str:
        """Extract text content from entity for AI processing"""
        text_parts = []
        
        # Add entity attributes that contain text
        attributes = entity.get('attributes', {})
        for key, value in attributes.items():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        text_parts.append(item)
                        
        return ' '.join(text_parts)
        
    def query_knowledge(self, question: str, context_entities: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query knowledge using AI"""
        try:
            # Build context from entities
            context = ""
            if context_entities:
                context_parts = []
                for entity in context_entities[:5]:  # Limit context size
                    entity_text = self._extract_text_from_entity(entity)
                    if entity_text:
                        context_parts.append(f"{entity.get('type', 'unknown')}: {entity_text[:200]}")
                context = "\n".join(context_parts)
                
            # Answer question using knowledge processor
            if context:
                qa_result = self.knowledge_processor.answer_question(question, context)
                
                # Also get conversational response
                chat_response = self.conversational_agent.chat(question, context)
                
                return {
                    'question': question,
                    'direct_answer': qa_result,
                    'conversational_response': chat_response,
                    'context_used': bool(context),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # No specific context, use conversational agent
                response = self.conversational_agent.chat(question)
                return {
                    'question': question,
                    'conversational_response': response,
                    'context_used': False,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error in knowledge query: {e}")
            return {
                'question': question,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded AI models"""
        info = {
            'model_name': self.model_name,
            'device': self.device,
            'transformers_available': TRANSFORMERS_AVAILABLE,
            'model_loaded': self.ai_model is not None
        }
        
        if self.ai_model:
            info['model_device'] = self.ai_model.device
            
        return info
        
    def set_model(self, model_name: str):
        """Change the AI model"""
        try:
            self.model_name = model_name
            self._initialize_components()
            self.logger.info(f"Switched to model: {model_name}")
        except Exception as e:
            self.logger.error(f"Error switching model: {e}")
            raise AIAgentError(f"Failed to switch model: {e}")


# Available models configuration
AVAILABLE_MODELS = {
    "distilbert-base-uncased": {
        "name": "DistilBERT Base",
        "type": "General Purpose",
        "size": "Small",
        "description": "Fast and lightweight model for general NLP tasks"
    },
    "bert-base-uncased": {
        "name": "BERT Base",
        "type": "General Purpose", 
        "size": "Medium",
        "description": "Standard BERT model for various NLP tasks"
    },
    "gpt2": {
        "name": "GPT-2",
        "type": "Text Generation",
        "size": "Medium",
        "description": "Text generation and conversational AI"
    },
    "facebook/bart-large-cnn": {
        "name": "BART Large CNN",
        "type": "Summarization",
        "size": "Large", 
        "description": "Specialized model for text summarization"
    }
}


def get_available_models() -> Dict[str, Dict[str, str]]:
    """Get list of available AI models"""
    return AVAILABLE_MODELS.copy()


if __name__ == "__main__":
    # Example usage
    try:
        agent = AIAgent()
        
        # Example entity processing
        entities = [{
            'id': 'doc_1',
            'type': 'document',
            'attributes': {
                'title': 'Project Requirements',
                'content': 'This document outlines the requirements for the new software project. The system should be scalable and user-friendly.'
            }
        }]
        
        processed = agent.process_entities(entities)
        print(f"Processed {len(processed)} entities")
        
        # Example knowledge query
        result = agent.query_knowledge("What are the project requirements?", processed)
        print(f"Query result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure to install required dependencies: pip install transformers torch")