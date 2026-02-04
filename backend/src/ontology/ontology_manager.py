import os
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
from rdflib.namespace import XSD
from typing import Optional, List, Dict, Any


class OntologyManager:
    """Upravlja Computer Use ontologijom"""
    
    # Namespace-ovi
    CU = Namespace("http://example.org/computer-use#")
    PROCESS = Namespace("http://www.daml.org/services/owl-s/1.2/Process.owl#")
    
    # Predefinisane akcije
    VALID_ACTIONS = [
        "click", "double_click", "right_click", "type_text",
        "key_press", "key_combination", "wait", "open_application",
        "close_application", "scroll", "move_mouse"
    ]
    
    def __init__(self, ontology_path: str = None):
        """
        Inicijalizuj ontology manager.
        
        Args:
            ontology_path: Putanja do .ttl fajla
        """
        self.graph = Graph()
        
        # Bind prefixes
        self.graph.bind("cu", self.CU)
        self.graph.bind("process", self.PROCESS)
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        
        # Pronadji putanju do ontologije
        if ontology_path is None:
            # Pokusaj nekoliko lokacija
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "..", "ontology", "computer_use.ttl"),
                os.path.join(os.getcwd(), "ontology", "computer_use.ttl"),
                os.path.join(os.getcwd(), "backend", "ontology", "computer_use.ttl"),
            ]
            
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    ontology_path = abs_path
                    break
        
        # Ucitaj ontologiju
        if ontology_path and os.path.exists(ontology_path):
            try:
                self.graph.parse(ontology_path, format="turtle")
                print(f"[OntologyManager] Loaded ontology: {len(self.graph)} triples")
                print(f"[OntologyManager] Path: {ontology_path}")
            except Exception as e:
                print(f"[OntologyManager] Error loading ontology: {e}")
                self._create_base_ontology()
        else:
            print(f"[OntologyManager] Ontology not found, creating a new one")
            self._create_base_ontology()
    
    def _create_base_ontology(self):
        """Kreiraj osnovnu strukturu ontologije"""
        # Dodaj osnovne klase
        self.graph.add((self.CU.Task, RDF.type, OWL.Class))
        self.graph.add((self.CU.Step, RDF.type, OWL.Class))
        self.graph.add((self.CU.Action, RDF.type, OWL.Class))
        self.graph.add((self.CU.UIElement, RDF.type, OWL.Class))
        self.graph.add((self.CU.Application, RDF.type, OWL.Class))
        
        # Dodaj akcije kao individuals
        for action in self.VALID_ACTIONS:
            action_uri = self.CU[action]
            self.graph.add((action_uri, RDF.type, self.CU.Action))
            self.graph.add((action_uri, RDFS.label, Literal(action)))
        
        print(f"[OntologyManager] Created base ontology with {len(self.graph)} triples")
    
    def get_valid_actions(self) -> List[str]:
        """Dobij listu validnih akcija"""
        
        # Probaj SPARQL upit
        query = """
        PREFIX cu: <http://example.org/computer-use#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT DISTINCT ?label WHERE {
            ?action rdf:type cu:Action .
            ?action rdfs:label ?label .
        }
        """
        
        try:
            results = list(self.graph.query(query))
            actions = [str(row.label) for row in results if row.label]
            
            if actions:
                print(f"[OntologyManager] Found {len(actions)} actions in ontology")
                return actions
        except Exception as e:
            print(f"[OntologyManager] SPARQL error: {e}")
        
        # Fallback - vrati predefinisane
        print(f"[OntologyManager] Using predefined actions")
        return self.VALID_ACTIONS.copy()
    
    def validate_action(self, action_name: str) -> bool:
        """Provjeri da li je akcija validna"""
        return action_name.lower() in [a.lower() for a in self.get_valid_actions()]
    
    def get_action_uri(self, action_name: str) -> URIRef:
        """Dobij URI akcije"""
        return self.CU[action_name]
    
    def add_task_to_graph(self, task_id: str, task_data: Dict[str, Any]) -> URIRef:
        """
        Dodaj task u graf.
        
        Args:
            task_id: Jedinstveni ID taska
            task_data: Dict sa goal, original_instruction, steps, itd.
            
        Returns:
            URI taska
        """
        task_uri = self.CU[f"Task_{task_id}"]
        
        # Dodaj osnovne triplete
        self.graph.add((task_uri, RDF.type, self.CU.Task))
        self.graph.add((task_uri, RDFS.label, Literal(f"Task {task_id}")))
        
        if task_data.get("goal"):
            self.graph.add((task_uri, self.CU.taskGoal, Literal(task_data["goal"])))
        
        if task_data.get("original_instruction"):
            self.graph.add((task_uri, self.CU.originalInstruction, 
                           Literal(task_data["original_instruction"])))
        
        if task_data.get("success_criteria"):
            self.graph.add((task_uri, self.CU.successCriteria, 
                           Literal(task_data["success_criteria"])))
        
        # Dodaj prerequisite-e
        for prereq in task_data.get("prerequisites", []):
            self.graph.add((task_uri, self.CU.hasPrerequisite, Literal(prereq)))
        
        # Dodaj korake
        steps = task_data.get("steps", [])
        previous_step_uri = None
        
        for step in steps:
            step_uri = self._add_step_to_graph(task_uri, step, previous_step_uri)
            previous_step_uri = step_uri
        
        print(f"[OntologyManager] Added Task: {task_uri}")
        print(f"[OntologyManager] Total triples: {len(self.graph)}")
        
        return task_uri
    
    def _add_step_to_graph(self, task_uri: URIRef, step: Dict[str, Any], 
                           previous_step: Optional[URIRef] = None) -> URIRef:
        """Dodaj korak u graf"""
        step_id = step.get("id", 0)
        step_uri = URIRef(f"{task_uri}_Step_{step_id}")
        
        # Osnovni triplete
        self.graph.add((step_uri, RDF.type, self.CU.Step))
        self.graph.add((task_uri, self.CU.hasStep, step_uri))
        self.graph.add((step_uri, self.CU.stepOrder, Literal(step_id, datatype=XSD.integer)))
        
        if step.get("description"):
            self.graph.add((step_uri, self.CU.stepDescription, Literal(step["description"])))
        
        if step.get("expected_result"):
            self.graph.add((step_uri, self.CU.expectedResult, Literal(step["expected_result"])))
        
        # Akcija
        action_name = step.get("action", "click")
        action_uri = self.CU[action_name]
        self.graph.add((step_uri, self.CU.hasAction, action_uri))
        
        # Target
        target = step.get("target", "")
        if target:
            self.graph.add((step_uri, self.CU.targetName, Literal(target)))
        
        # Value - zavisno od akcije
        value = step.get("value")
        if value:
            if action_name == "wait":
                try:
                    wait_val = int(value)
                    self.graph.add((step_uri, self.CU.waitDuration, 
                                   Literal(wait_val, datatype=XSD.integer)))
                except:
                    self.graph.add((step_uri, self.CU.inputValue, Literal(value)))
            elif action_name in ["type_text"]:
                self.graph.add((step_uri, self.CU.inputValue, Literal(value)))
            elif action_name in ["key_press", "key_combination"]:
                self.graph.add((step_uri, self.CU.keyName, Literal(value)))
            else:
                self.graph.add((step_uri, self.CU.inputValue, Literal(value)))
        
        # Sekvenca koja je veza sa prethodnim korakom
        if previous_step:
            self.graph.add((previous_step, self.CU.nextStep, step_uri))
            self.graph.add((step_uri, self.CU.previousStep, previous_step))
        
        # Pocetno stanje
        self.graph.add((step_uri, self.CU.hasState, self.CU.PendingState))
        
        return step_uri
    
    def get_task_steps(self, task_uri: URIRef) -> List[Dict[str, Any]]:
        """Dobija sve korake za task, sortirane po redoslijedu"""
        
        query = f"""
        PREFIX cu: <http://example.org/computer-use#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?step ?order ?action ?target ?description ?expected ?inputVal ?waitVal ?keyVal WHERE {{
            <{task_uri}> cu:hasStep ?step .
            ?step cu:stepOrder ?order .
            ?step cu:hasAction ?action .
            OPTIONAL {{ ?step cu:targetName ?target }}
            OPTIONAL {{ ?step cu:stepDescription ?description }}
            OPTIONAL {{ ?step cu:expectedResult ?expected }}
            OPTIONAL {{ ?step cu:inputValue ?inputVal }}
            OPTIONAL {{ ?step cu:waitDuration ?waitVal }}
            OPTIONAL {{ ?step cu:keyName ?keyVal }}
        }}
        ORDER BY ?order
        """
        
        results = self.graph.query(query)
        steps = []
        
        for row in results:
            # Odredi value zavisno od tipa akcije
            value = None
            if row.inputVal:
                value = str(row.inputVal)
            elif row.waitVal:
                value = str(row.waitVal)
            elif row.keyVal:
                value = str(row.keyVal)
            
            steps.append({
                "uri": str(row.step),
                "id": int(row.order),
                "action": str(row.action).split("#")[-1],
                "target": str(row.target) if row.target else "",
                "value": value,
                "description": str(row.description) if row.description else "",
                "expected_result": str(row.expected) if row.expected else ""
            })
        
        return steps
    
    def update_step_state(self, step_uri: URIRef, state: str):
        """Azuriraj stanje koraka"""
        state_map = {
            "pending": self.CU.PendingState,
            "executing": self.CU.ExecutingState,
            "completed": self.CU.CompletedState,
            "failed": self.CU.FailedState,
            "skipped": self.CU.SkippedState
        }
        
        state_uri = state_map.get(state.lower(), self.CU.PendingState)
        
        # Ukloni staro stanje
        if isinstance(step_uri, str):
            step_uri = URIRef(step_uri)
        
        self.graph.remove((step_uri, self.CU.hasState, None))
        
        # Dodaj novo stanje
        self.graph.add((step_uri, self.CU.hasState, state_uri))
    
    def save_ontology(self, path: str, format: str = "turtle"):
        """
        Sacuvaj ontologiju.
        
        Args:
            path: Putanja za cuvanje
            format: Format (turtle, xml, n3)
        """
        # Kreiraj folder ako ne postoji
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        
        # Odredi format na osnovu ekstenzije
        if path.endswith(".owl"):
            format = "xml"
        elif path.endswith(".ttl"):
            format = "turtle"
        elif path.endswith(".n3"):
            format = "n3"
        
        self.graph.serialize(destination=path, format=format)
        print(f"[OntologyManager] Ontology saved: {path}")
        print(f"[OntologyManager] Format: {format}, Triples: {len(self.graph)}")