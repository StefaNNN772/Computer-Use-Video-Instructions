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
        """Parsira korisnički tekstualni opis."""
        
        prompt = f"""Analiziraj sledece korisnicko uputstvo za kreiranje video tutorijala o programiranju.

                        KORISNIcKO UPUTSTVO: 
                        "{user_instruction}"

                        Tvoj zadatak je da izvuces kljucne informacije iz ovog uputstva. 

                        Odgovori ISKLJUCIVO u JSON formatu sa sledecom strukturom:
                        {{
                            "intent": "Kratak opis sta korisnik zeli postici",
                            "application":  "Naziv aplikacije koja se koristi (npr. Eclipse, VS Code, IntelliJ, Terminal)",
                            "programming_language": "Programski jezik ako je naveden, inace null",
                            "specific_actions": [
                                "Lista konkretnih akcija koje treba izvrsiti",
                                "Svaka akcija kao poseban string"
                            ]
                        }}

                        VAZNO: Odgovori SAMO sa JSON objektom, bez dodatnog teksta, bez markdown formatiranja."""

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