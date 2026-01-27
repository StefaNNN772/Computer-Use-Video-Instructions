# from groq import Groq
# import json
# import os
# from dotenv import load_dotenv
# from . models import ParsedInput, TaskPlan, Step, ActionType

# load_dotenv()

# class TaskDecomposer: 
#     """Deli parsirani zadatak na manje, atomicne korake"""
    
#     def __init__(self):
#         api_key = os.getenv("GROQ_API_KEY")
#         if not api_key:
#             raise ValueError("GROQ_API_KEY is not set in the .env file!")
        
#         self. client = Groq(api_key=api_key)
#         self.model = "llama-3.3-70b-versatile"
    
#     def decompose(self, parsed_input: ParsedInput) -> TaskPlan:
#         """Prima parsirani input i vraca detaljan plan izvrsavanja"""
        
#         action_types = ", ".join([at.value for at in ActionType])
        
#         prompt = f"""Ti si ekspert za automatizaciju desktop aplikacija.  Kreiraj DETALJAN plan za Computer Use AI agenta. 

#                     KONTEKST:
#                     - Cilj: {parsed_input.intent}
#                     - Aplikacija: {parsed_input.application}
#                     - Programski jezik: {parsed_input.programming_language or "Nije specificirano"}
#                     - Akcije: {json.dumps(parsed_input.specific_actions, ensure_ascii=False)}

#                     DOSTUPNE AKCIJE:
#                     {action_types}

#                     ═══════════════════════════════════════════════════════════════════════════
#                     KRITIČNA PRAVILA ZA KREIRANJE KORAKA:
#                     ═══════════════════════════════════════════════════════════════════════════

#                     1. TARGET MORA BITI TAČAN TEKST koji se VIDI na ekranu (na ENGLESKOM za IDE):
#                     DOBRO:  "File", "New", "Project.. .", "Console App", "Next", "Create"
#                     LOŠE: "File menu", "New project button", "klikni na File"

#                     2. Za MENIJE - svaki nivo je POSEBAN KORAK:
#                     - Korak 1: click na "File"
#                     - Korak 2: click na "New" 
#                     - Korak 3: click na "Project..."
                    
#                     3. Za ČEKANJE - value je BROJ (ne tekst):
#                     DOBRO: "value": "3"
#                     LOŠE: "value":  "3 sekunde"

#                     4. Za TYPE_TEXT: 
#                     - target = ime polja (npr. "Project name") ili "editor" za kod
#                     - value = tekst za unos

#                     5. OBAVEZNI WAIT koraci:
#                     - Nakon open_application:  wait 4 sekunde
#                     - Nakon kreiranja projekta: wait 3 sekunde
#                     - Nakon klika na meni: wait 1 sekunda

#                     6. Za Visual Studio 2022:
#                     - Start:  otvara se Start Window
#                     - "Create a new project" dugme na Start Window
#                     - Search box za template:  ukucaj "Console"
#                     - Izaberi "Console App" (sa C# ikonom)
#                     - "Next" dugme
#                     - "Project name" input polje
#                     - "Create" dugme
#                     - Čekaj da se projekat učita
#                     - Kod se piše u EDITORU (ne treba klikati - editor je već fokusiran)
#                     - Za RUN: klikni na zeleno "Start" dugme ili pritisni F5

#                     7. Za Eclipse:
#                     - File > New > Java Project
#                     - Unesi ime projekta
#                     - Finish
#                     - Desni klik na "src" folder
#                     - New > Class
#                     - Unesi ime klase, čekiraj "public static void main"
#                     - Finish
#                     - Piši kod
#                     - Run > Run ili Ctrl+F11

#                     ═══════════════════════════════════════════════════════════════════════════
#                     PRIMJER ZA VISUAL STUDIO C# KONZOLNU APLIKACIJU: 
#                     ═══════════════════════════════════════════════════════════════════════════

#                     {{
#                     "goal": "Kreiranje C# konzolne aplikacije koja ispisuje Hello World",
#                     "prerequisites": ["Visual Studio 2022 je instaliran"],
#                     "steps": [
#                         {{"id": 1, "action":  "open_application", "target": "Visual Studio", "value": null, "description": "Pokreni Visual Studio", "expected_result": "Visual Studio Start Window je otvoren"}},
#                         {{"id":  2, "action": "wait", "target": "screen", "value": "10", "description": "Cekaj ucitavanje", "expected_result":  "Start Window je vidljiv"}},
#                         {{"id": 3, "action": "click", "target": "Create a new project", "value": null, "description": "Klikni Create a new project", "expected_result": "Template selection dialog je otvoren"}},
#                         {{"id":  4, "action": "wait", "target": "screen", "value": "2", "description": "Cekaj dialog", "expected_result":  "Template lista je vidljiva"}},
#                         {{"id": 5, "action": "type_text", "target":  "Search for templates", "value": "Console", "description":  "Pretrazi Console template", "expected_result": "Console App template je vidljiv"}},
#                         {{"id": 6, "action": "wait", "target": "screen", "value":  "2", "description": "Cekaj rezultate pretrage", "expected_result": "Console App je prikazan"}},
#                         {{"id": 7, "action":  "click", "target": "Console App", "value": null, "description": "Izaberi Console App template", "expected_result": "Console App je selektovan"}},
#                         {{"id": 8, "action": "click", "target": "Next", "value": null, "description": "Klikni Next", "expected_result": "Configure project dialog je otvoren"}},
#                         {{"id": 9, "action": "wait", "target": "screen", "value":  "1", "description": "Cekaj dialog", "expected_result": "Project name polje je vidljivo"}},
#                         {{"id": 10, "action": "click", "target": "Project name", "value":  null, "description":  "Klikni na Project name polje", "expected_result": "Polje je aktivno"}},
#                         {{"id": 11, "action":  "key_combination", "target": "ctrl+a", "value": null, "description": "Selektuj sav tekst", "expected_result": "Tekst je selektovan"}},
#                         {{"id": 12, "action": "type_text", "target": "editor", "value": "HelloWorld", "description":  "Unesi ime projekta", "expected_result": "HelloWorld je uneseno"}},
#                         {{"id": 13, "action": "click", "target": "Next", "value":  null, "description":  "Klikni Next", "expected_result": "Framework selection je otvoren"}},
#                         {{"id": 14, "action": "wait", "target": "screen", "value": "1", "description":  "Cekaj", "expected_result":  "Framework opcije su vidljive"}},
#                         {{"id": 15, "action": "click", "target": "Create", "value": null, "description": "Klikni Create", "expected_result": "Projekat se kreira"}},
#                         {{"id": 16, "action":  "wait", "target": "screen", "value": "8", "description": "Cekaj kreiranje projekta", "expected_result": "Editor sa Program. cs je otvoren"}},
#                         {{"id":  17, "action": "click", "target": "Program.cs", "value": null, "description": "Klikni na Program.cs tab", "expected_result":  "Program.cs je aktivan"}},
#                         {{"id": 18, "action":  "key_combination", "target": "ctrl+a", "value": null, "description": "Selektuj sav kod", "expected_result": "Kod je selektovan"}},
#                         {{"id": 19, "action": "type_text", "target":  "editor", "value": "Console. WriteLine(\\"Hello World! \\");", "description": "Unesi Hello World kod", "expected_result": "Kod je unesen"}},
#                         {{"id": 20, "action": "key_combination", "target": "ctrl+s", "value": null, "description": "Sacuvaj fajl", "expected_result": "Fajl je sacuvan"}},
#                         {{"id": 21, "action": "wait", "target": "screen", "value":  "1", "description": "Cekaj", "expected_result":  "Spremno za pokretanje"}},
#                         {{"id":  22, "action": "key_press", "target": "f5", "value":  null, "description":  "Pokreni aplikaciju (F5)", "expected_result": "Aplikacija se pokrece"}},
#                         {{"id": 23, "action": "wait", "target":  "screen", "value": "5", "description": "Cekaj izvrsavanje", "expected_result": "Hello World je ispisan u konzoli"}}
#                     ],
#                     "success_criteria": "Hello World!  je prikazan u konzoli"
#                     }}

#                     ═══════════════════════════════════════════════════════════════════════════

#                     Sada kreiraj plan za dati zadatak.  Odgovori SAMO sa JSON objektom. 
#                     VAŽNO: value za wait MORA biti broj kao string (npr. "5"), NE "5 sekundi"! 
#                     VAŽNO: target MORA biti TAČAN tekst koji se vidi na UI-u! 
#                     VAZNO: Proveri DA LI JE SVE TAČNO pre slanja odgovora!
#                     VAZNO: Vodi racuna da se radi o najnovijim verzijama aplikacija (npr. Visual Studio 2026).
#                     VAZNO: Detaljno idi korak po korak, NIKADA NE PRESKAČI KORAKE."""

#         response = self.client.chat. completions.create(
#             model=self.model,
#             messages=[{"role":  "user", "content": prompt}],
#             max_tokens=4096,
#             temperature=0.3
#         )
        
#         response_text = response.choices[0].message.content. strip()
        
#         # Ocisti markdown formatiranje
#         if "```json" in response_text:
#             response_text = response_text.split("```json")[1].split("```")[0]
#         elif "```" in response_text:
#             response_text = response_text.split("```")[1].split("```")[0]
        
#         response_text = response_text.strip()
        
#         try: 
#             plan_data = json.loads(response_text)
#         except json. JSONDecodeError as e:
#             print(f"Error while parsing JSON: {e}")
#             print(f"Response: {response_text[: 500]}...")
#             raise
        
#         # Konvertuj u Step objekte
#         steps = []
#         for step_data in plan_data["steps"]: 
#             try: 
#                 action = ActionType(step_data["action"])
#             except ValueError:
#                 print(f"Unknown action '{step_data['action']}', using 'click'")
#                 action = ActionType. CLICK
            
#             target = step_data. get("target")
#             if target is None or target == "": 
#                 target = "screen"
            
#             value = step_data.get("value")
#             if value is not None and not isinstance(value, str):
#                 value = str(value)
            
#             steps.append(Step(
#                 id=step_data["id"],
#                 action=action,
#                 target=target,
#                 value=value,
#                 description=step_data. get("description", ""),
#                 expected_result=step_data.get("expected_result", "Action is successfully completed")
#             ))
        
#         return TaskPlan(
#             original_instruction=parsed_input. raw_input,
#             goal=plan_data["goal"],
#             prerequisites=plan_data["prerequisites"],
#             steps=steps,
#             success_criteria=plan_data["success_criteria"]
#         )
    
#     def print_plan(self, plan:  TaskPlan) -> None:
#         """Stampa plan u citljivom formatu"""
        
#         print("\n" + "=" * 70)
#         print("Plan of execution:")
#         print("=" * 70)
#         print(f"\nGoal: {plan.goal}")
#         print(f"\nOriginal instruction: {plan.original_instruction}")
        
#         print(f"\nPrerequisites:")
#         for prereq in plan.prerequisites:
#             print(f"   • {prereq}")
        
#         print(f"\nSteps ({len(plan.steps)} total):")
#         print("-" * 70)
        
#         for step in plan.steps:
#             action_label = {
#                 ActionType.CLICK:  "[CLICK]",
#                 ActionType.DOUBLE_CLICK: "[DBL-CLICK]",
#                 ActionType.TYPE_TEXT:  "[TYPE]",
#                 ActionType.KEY_PRESS: "[KEY]",
#                 ActionType.KEY_COMBINATION: "[COMBO]",
#                 ActionType.WAIT: "[WAIT]",
#                 ActionType. OPEN_APPLICATION: "[OPEN]",
#                 ActionType.SCROLL: "[SCROLL]",
#                 ActionType.RIGHT_CLICK: "[R-CLICK]",
#                 ActionType. MOVE_MOUSE: "[MOVE]"
#             }.get(step.action, "[ACTION]")
            
#             print(f"\n  [{step.id:2d}] {action_label} {step. action. value. upper()}")
#             print(f"Target: {step.target}")
#             if step.value:
#                 print(f"Value: {step.value}")
#             print(f"{step.description}")
#             print(f"Expected: {step. expected_result}")
        
#         print("\n" + "-" * 70)
#         print(f"Success criteria: {plan. success_criteria}")
#         print("=" * 70 + "\n")
from groq import Groq
import json
import os
import re
from dotenv import load_dotenv
from .models import ParsedInput, TaskPlan, Step, ActionType
from .ontology import OntologyManager, PlanValidator

load_dotenv()


class TaskDecomposer:
    """Kreira i validira plan koristeci ontologiju"""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY nije postavljen!")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
        # Ontologija za validaciju
        self.ontology = OntologyManager()
        self.validator = PlanValidator(self.ontology)
        
        # Dobija validne akcije iz ontologije
        self.valid_actions = self.ontology.get_valid_actions()
        print(f"[TaskDecomposer] Validne akcije: {', '.join(self.valid_actions)}")
    
    def decompose(self, parsed_input: ParsedInput) -> TaskPlan:
        """Kreira plan i validira ga prema ontologiji."""
        
        # Kreiraj prompt sa validnim akcijama iz ontologije
        action_types = ", ".join(self.valid_actions)
        
        prompt = self._create_prompt(parsed_input, action_types)
        
        # Pozovi LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parsiraj JSON
        plan_data = self._parse_response(response_text)
        
        # Validiraj prema ontologiji
        print("\n[TaskDecomposer] Validating plan against ontology...")
        validation = self.validator.get_validation_report(plan_data)
        
        if not validation["is_valid"]:
            print("[TaskDecomposer] Plan has errors, attempting to fix...")
            for error in validation["errors"]:
                print(f"Error: {error}")
            plan_data = self._fix_plan(plan_data, validation["errors"])
        
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"Warning: {warning}")
        
        print(f"[TaskDecomposer] Plan created with {len(plan_data.get('steps', []))} steps")
        
        # Konvertuj u TaskPlan objekt
        return self._create_task_plan(plan_data, parsed_input)
    
    def _create_prompt(self, parsed_input: ParsedInput, action_types: str) -> str:
        """Kreiraj detaljan prompt za LLM."""
        
        return f"""You are an expert in desktop application automation. Create a DETAILED plan for a Computer Use AI agent.
                    CONTEXT:
                    - Goal: {parsed_input.intent}
                    - Application: {parsed_input.application}
                    - Programming language: {parsed_input.programming_language or "Not specified"}
                    - Actions: {json.dumps(parsed_input.specific_actions, ensure_ascii=False)}

                    AVAILABLE ACTIONS:
                    {action_types}

                    ═══════════════════════════════════════════════════════════════════════════
                    CRITICAL RULES FOR CREATING STEPS:
                    ═══════════════════════════════════════════════════════════════════════════

                    1. TARGET MUST BE THE EXACT TEXT that is VISIBLE on the screen (IN ENGLISH for IDEs):
                    GOOD: "File", "New", "Project...", "Console App", "Next", "Create"
                    BAD: "File menu", "New project button", "click File"

                    2. For MENUS – each level is a SEPARATE STEP:
                    - Step 1: click on "File"
                    - Step 2: click on "New"
                    - Step 3: click on "Project..."

                    3. For WAIT – value must be a NUMBER (not text):
                    GOOD: "value": "3"
                    BAD: "value": "3 seconds"

                    4. For TYPE_TEXT:
                    - target = field name (e.g. "Project name") or "editor" for code
                    - value = text to input

                    5. MANDATORY WAIT STEPS:
                    - After open_application: wait 5 seconds
                    - After project creation: wait 6 seconds
                    - After clicking a menu: wait 1 second

                    6. For Visual Studio 2022/2026:
                    - Start: Start Window opens
                    - "Create a new project" button on Start Window
                    - Template search box: type "Console"
                    - Select "Console App" (with C# icon)
                    - "Next" button
                    - "Project name" input field
                    - "Create" button
                    - Wait for project to load
                    - Code is written in the EDITOR (no need to click – editor is already focused)
                    - To RUN: click the green "Start" button or press F5

                    7. For Eclipse:
                    - File > New > Java Project
                    - Enter project name
                    - Finish
                    - Right click on "src" folder
                    - New > Class
                    - Enter class name, check "public static void main"
                    - Finish
                    - Write code
                    - Run > Run or Ctrl+F11

                    8. For Browsers (Chrome, Firefox, Opera, Edge):
                    - open_application to launch the browser
                    - wait 4 seconds for loading
                    - type_text in "Address bar" for the URL
                    - key_press "enter" to navigate
                    - wait for page load
                    - For YouTube: type_text in "Search" field, key_press "enter", click on a result

                    ═══════════════════════════════════════════════════════════════════════════
                    EXAMPLE FOR VISUAL STUDIO C# CONSOLE APPLICATION:
                    ═══════════════════════════════════════════════════════════════════════════

                    {{
                    "goal": "Create a C# console application that prints Hello World",
                    "prerequisites": ["Visual Studio 2022 is installed"],
                    "steps": [
                        {{"id": 1, "action":  "open_application", "target": "Visual Studio", "value": null, "description": "Start Visual Studio", "expected_result": "Visual Studio Start Window is opened"}},
#                         {{"id":  2, "action": "wait", "target": "screen", "value": "10", "description": "Wait for loading", "expected_result":  "Start Window is visible"}},
#                         {{"id": 3, "action": "click", "target": "Create a new project", "value": null, "description": "Click Create a new project", "expected_result": "Template selection dialog is opened"}},
#                         {{"id":  4, "action": "wait", "target": "screen", "value": "2", "description": "Wait for dialog", "expected_result":  "Template list is visible"}},
#                         {{"id": 5, "action": "type_text", "target":  "Search for templates", "value": "Console", "description":  "Search Console template", "expected_result": "Console App template is visible"}},
#                         {{"id": 6, "action": "wait", "target": "screen", "value":  "2", "description": "Wait for search results", "expected_result": "Console App is displayed"}},
#                         {{"id": 7, "action":  "click", "target": "Console App", "value": null, "description": "Select Console App template", "expected_result": "Console App is selected"}},
#                         {{"id": 8, "action": "click", "target": "Next", "value": null, "description": "Click Next", "expected_result": "Configure project dialog is opened"}},
#                         {{"id": 9, "action": "wait", "target": "screen", "value":  "1", "description": "Wait for dialog", "expected_result": "Project name field is visible"}},
#                         {{"id": 10, "action": "click", "target": "Project name", "value":  null, "description":  "Click on Project name field", "expected_result": "Field is active"}},
#                         {{"id": 11, "action":  "key_combination", "target": "ctrl+a", "value": null, "description": "Select all text", "expected_result": "Text is selected"}},
#                         {{"id": 12, "action": "type_text", "target": "editor", "value": "HelloWorld", "description":  "Input project name", "expected_result": "HelloWorld is entered"}},
#                         {{"id": 13, "action": "click", "target": "Next", "value":  null, "description":  "Click Next", "expected_result": "Framework selection is opened"}},
#                         {{"id": 14, "action": "wait", "target": "screen", "value": "1", "description":  "Wait", "expected_result":  "Framework options are visible"}},
#                         {{"id": 15, "action": "click", "target": "Create", "value": null, "description": "Click Create", "expected_result": "Project is created"}},
#                         {{"id": 16, "action":  "wait", "target": "screen", "value": "8", "description": "Wait for project creation", "expected_result": "Editor with Program.cs is opened"}},
#                         {{"id":  17, "action": "click", "target": "Program.cs", "value": null, "description": "Click on Program.cs tab", "expected_result":  "Program.cs is active"}},
#                         {{"id": 18, "action":  "key_combination", "target": "ctrl+a", "value": null, "description": "Select all code", "expected_result": "Code is selected"}},
#                         {{"id": 19, "action": "type_text", "target":  "editor", "value": "Console. WriteLine(\\"Hello World! \\");", "description": "Input Hello World code", "expected_result": "Code is entered"}},
#                         {{"id": 20, "action": "key_combination", "target": "ctrl+s", "value": null, "description": "Save file", "expected_result": "File is saved"}},
#                         {{"id": 21, "action": "wait", "target": "screen", "value":  "1", "description": "Wait", "expected_result":  "Ready to run"}},
#                         {{"id":  22, "action": "key_press", "target": "f5", "value":  null, "description":  "Run application (F5)", "expected_result": "Application is running"}},
#                         {{"id": 23, "action": "wait", "target":  "screen", "value": "5", "description": "Wait for execution", "expected_result": "Hello World is displayed in the console"}}
                    ],
                    "success_criteria": "Hello World! is displayed in the console"
                    }}

                    ═══════════════════════════════════════════════════════════════════════════

                    Now create a plan for the given task. Respond ONLY with a JSON object.

                    IMPORTANT: wait value MUST be a number as a string (e.g. "5"), NOT "5 seconds"!
                    IMPORTANT: target MUST be the EXACT text visible in the UI!
                    IMPORTANT: Verify EVERYTHING before sending the response!
                    IMPORTANT: Assume the latest versions of applications (e.g. Visual Studio 2026).
                    IMPORTANT: Go step by step in detail, NEVER SKIP STEPS!
                    IMPORTANT: Add wait after EVERY action that requires loading!"""

    def _parse_response(self, response_text: str) -> dict:
        # Ocisti markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        response_text = response_text.strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[TaskDecomposer] JSON parse error: {e}")
            print(f"[TaskDecomposer] Response: {response_text[:500]}...")
            raise
    
    def _fix_plan(self, plan_data: dict, errors: list) -> dict:
        for step in plan_data.get("steps", []):
            action = step.get("action", "")
            
            # Ispravi nepoznate akcije
            if action not in self.valid_actions:
                print(f"[FIX] Unknown action '{action}' -> 'click'")
                step["action"] = "click"
            
            # Dodaj value za wait ako nedostaje
            if action == "wait" and not step.get("value"):
                step["value"] = "4"
            
            # Ocisti value za wait (ukloni "sekundi", "seconds", itd.)
            if action == "wait" and step.get("value"):
                value = str(step["value"])
                numbers = re.findall(r'\d+', value)
                if numbers:
                    step["value"] = numbers[0]
                else:
                    step["value"] = "4"
            
            # Dodaj target ako nedostaje
            if not step.get("target"):
                step["target"] = "screen"
        
        return plan_data
    
    def _create_task_plan(self, plan_data: dict, parsed_input: ParsedInput) -> TaskPlan:
        steps = []
        for step_data in plan_data.get("steps", []):
            try:
                action = ActionType(step_data["action"])
            except ValueError:
                print(f"[TaskDecomposer] Unknown action: {step_data['action']}, using CLICK")
                action = ActionType.CLICK
            
            value = step_data.get("value")
            if value is not None:
                value = str(value)
                # Za wait, ocisti value
                if action == ActionType.WAIT:
                    numbers = re.findall(r'\d+', value)
                    value = numbers[0] if numbers else "4"
            
            steps.append(Step(
                id=step_data.get("id", len(steps) + 1),
                action=action,
                target=step_data.get("target", "screen"),
                value=value,
                description=step_data.get("description", ""),
                expected_result=step_data.get("expected_result", "")
            ))
        
        return TaskPlan(
            original_instruction=parsed_input.raw_input,
            goal=plan_data.get("goal", ""),
            prerequisites=plan_data.get("prerequisites", []),
            steps=steps,
            success_criteria=plan_data.get("success_criteria", "")
        )
    
    # def print_plan(self, plan: TaskPlan):
    #     print("\n" + "=" * 70)
    #     print("   GENERISANI PLAN")
    #     print("=" * 70)
    #     print(f"\n   Cilj: {plan.goal}")
    #     print(f"   Originalna instrukcija: {plan.original_instruction}")
        
    #     print(f"\n   Preduslovi:")
    #     for prereq in plan.prerequisites:
    #         print(f"      • {prereq}")
        
    #     print(f"\n   Koraci ({len(plan.steps)}):")
    #     print("   " + "-" * 65)
        
    #     action_icons = {
    #         ActionType.CLICK: "🖱️",
    #         ActionType.DOUBLE_CLICK: "🖱️🖱️",
    #         ActionType.TYPE_TEXT: "⌨️",
    #         ActionType.KEY_PRESS: "⌨️",
    #         ActionType.KEY_COMBINATION: "⌨️",
    #         ActionType.WAIT: "⏳",
    #         ActionType.OPEN_APPLICATION: "🚀",
    #         ActionType.SCROLL: "📜",
    #         ActionType.RIGHT_CLICK: "🖱️",
    #     }
        
    #     for step in plan.steps:
    #         icon = action_icons.get(step.action, "•")
            
    #         print(f"\n   [{step.id:2d}] {icon} {step.action.value.upper()}")
    #         print(f"        Target: {step.target}")
    #         if step.value:
    #             print(f"        Value: {step.value}")
    #         print(f"        {step.description}")
        
    #     print("\n   " + "-" * 65)
    #     print(f"   Kriterijum uspjeha: {plan.success_criteria}")
    #     print("=" * 70 + "\n")

    def print_plan(self, plan:  TaskPlan) -> None:
        """Stampa plan u citljivom formatu"""
        
        print("\n" + "=" * 70)
        print("Plan of execution:")
        print("=" * 70)
        print(f"\nGoal: {plan.goal}")
        print(f"\nOriginal instruction: {plan.original_instruction}")
        
        print(f"\nPrerequisites:")
        for prereq in plan.prerequisites:
            print(f"====> {prereq}")
        
        print(f"\nSteps ({len(plan.steps)} total):")
        print("-" * 70)
        
        for step in plan.steps:
            action_label = {
                ActionType.CLICK:  "[CLICK]",
                ActionType.DOUBLE_CLICK: "[DBL-CLICK]",
                ActionType.TYPE_TEXT:  "[TYPE]",
                ActionType.KEY_PRESS: "[KEY]",
                ActionType.KEY_COMBINATION: "[COMBO]",
                ActionType.WAIT: "[WAIT]",
                ActionType.OPEN_APPLICATION: "[OPEN]",
                ActionType.SCROLL: "[SCROLL]",
                ActionType.RIGHT_CLICK: "[R-CLICK]",
                ActionType.MOVE_MOUSE: "[MOVE]"
            }.get(step.action, "[ACTION]")
            
            print(f"\n  [{step.id:2d}] {action_label} {step. action. value. upper()}")
            print(f"Target: {step.target}")
            if step.value:
                print(f"Value: {step.value}")
            print(f"{step.description}")
            print(f"Expected: {step. expected_result}")
        
        print("\n" + "-" * 70)
        print(f"Success criteria: {plan. success_criteria}")
        print("=" * 70 + "\n")