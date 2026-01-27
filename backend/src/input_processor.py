from groq import Groq
import json
import os
from dotenv import load_dotenv
from . models import ParsedInput

load_dotenv()

class InputProcessor:
    """Groq parsira tekstualni opis korisnika"""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key: 
            raise ValueError("GROQ_API_KEY is not set in the .env file!")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        print(f"Groq initialized (model: {self.model})")
    
    def parse(self, user_instruction: str) -> ParsedInput:
        """Parsira korisnicki tekstualni opis"""
        
        prompt = f"""Analyze the following user instruction for creating a programming video tutorial.

                        USER INSTRUCTION:
                        "{user_instruction}"

                        Your task is to extract key information from this instruction.

                        Respond EXCLUSIVELY in JSON format with the following structure:
                        {{
                            "intent": "A brief description of what the user wants to achieve",
                            "application": "Name of the application being used (e.g. Eclipse, VS Code, IntelliJ, Terminal)",
                            "programming_language": "Programming language if mentioned, otherwise null",
                            "specific_actions": [
                                "List of specific actions that need to be performed",
                                "Each action as a separate string"
                            ]
                        }}

                        IMPORTANT: Respond ONLY with the JSON object, without additional text, without markdown formatting."""

        response = self. client.chat.completions.create(
            model=self. model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3
        )
        
        response_text = response. choices[0].message.content. strip()
        
        # Ocisti ako ima markdown formatiranje
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        response_text = response_text. strip()
        
        try:
            parsed_data = json. loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error while parsing JSON: {e}")
            print(f"Response:  {response_text}")
            raise
        
        return ParsedInput(
            raw_input=user_instruction,
            intent=parsed_data["intent"],
            application=parsed_data["application"],
            programming_language=parsed_data.get("programming_language"),
            specific_actions=parsed_data["specific_actions"]
        )
    
    def validate_input(self, user_instruction: str) -> tuple[bool, str]: 
        """Provjerava da li je korisnicki unos validan"""
        
        if not user_instruction or len(user_instruction. strip()) < 10:
            return False, "Instruction is too short. Please provide more details."
        
        programming_keywords = [
            "projekat", "project", "kod", "code", "program",
            "eclipse", "vs code", "visual studio", "intellij",
            "java", "python", "javascript", "c++", "c#",
            "kompajl", "compile", "run", "pokreni", "debug",
            "klasa", "class", "funkcija", "function", "metoda",
            "tutorial", "uputstvo", "napravi", "kreiraj"
        ]
        
        lower_input = user_instruction. lower()
        if not any(keyword in lower_input for keyword in programming_keywords):
            return False, "The instruction doen not seem to be related to programming tasks"
        
        return True, "OK"