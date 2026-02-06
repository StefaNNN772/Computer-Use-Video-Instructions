# Computer Use Video Instructions

An automated system for generating video tutorials by executing step-by-step instructions on desktop applications. The system leverages Large Language Models (LLMs) for natural language understanding and task decomposition, computer vision for UI element detection, and an OWL ontology for knowledge representation, plan validation, and execution control.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Ontology Design](#ontology-design)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Limitations](#limitations)
- [License](#license)

## Overview

This project automates the creation of video tutorials for desktop applications. Users provide natural language instructions (e.g., "Create a C# console application in Visual Studio that prints Hello World"), and the system:

1. Parses the instruction using an LLM (Groq - Llama 3.3 70B) to extract intent, target application, and required actions
2. Generates a detailed step-by-step execution plan in JSON format
3. Maps the JSON plan to an OWL ontology for semantic representation
4. Validates the plan against ontology-defined rules and constraints
5. Executes the plan by reading steps from the OWL file using SPARQL queries
6. Uses computer vision (OpenRouter - Qwen 2.5 VL 72B) to locate UI elements on screen
7. Controls mouse and keyboard inputs via PyAutoGUI
8. Records the entire execution (FFmpeg) as an MP4 video tutorial

## Features

- Natural language instruction processing
- Automatic task plan generation using LLM
- OWL ontology-based plan representation and validation
- SPARQL-based step extraction for execution
- Vision-based UI element detection
- Cross-application automation (Visual Studio, VS Code, browsers, etc.)
- Screen recording with FFmpeg
- Web-based frontend for plan editing and video playback
- Tutorial library for managing saved tutorials

## Ontology Design

The system uses an OWL (Web Ontology Language) ontology defined in Turtle format (`computer_use.ttl`) as the central knowledge representation mechanism. The ontology serves three primary purposes:

### 1. Knowledge Representation

The ontology defines the domain vocabulary for desktop automation:

**Core Classes:**
- `Task` - Represents a complete automation task (composite process)
- `Step` - Represents an atomic action within a task
- `Action` - Types of actions that can be performed
- `UIElement` - User interface elements (buttons, text fields, menus)
- `Application` - Desktop applications (browsers, IDEs, editors)
- `ExecutionState` - States of step execution (Pending, Executing, Completed, Failed)

**Object Properties:**
- `hasStep` - Links Task to its Steps
- `hasAction` - Links Step to its Action type
- `hasTarget` - Links Step to target UIElement
- `hasState` - Links Step to its ExecutionState
- `nextStep` / `previousStep` - Sequential ordering of steps
- `requiresApplication` - Application dependencies

**Data Properties:**
- `stepOrder` - Integer order of step execution
- `stepDescription` - Human-readable description
- `targetName` - Name of the target UI element
- `inputValue` - Value for text input actions
- `waitDuration` - Duration for wait actions
- `expectedResult` - Expected outcome of step

### 2. Plan Validation

The ontology enables rule-based validation of execution plans:

| Rule                  | Description                                                 |
|-----------------------|-------------------------------------------------------------|
| Action Validation     | Only ontology-defined actions are allowed                   |
| Sequence Validation   | `open_application` should precede application interactions  |
| Wait Recommendation   | `wait` should follow `open_application`                     |
| Parameter Validation  | `type_text` requires `value`, `key_press` requires key name |
| Target Validation     | `click` actions should have specific targets                |

### 3. Execution Control

Steps are executed by reading directly from the OWL file:

```python
# SPARQL query to extract steps from ontology
query = """
PREFIX cu: <http://example.org/computer-use#>

SELECT ?step ?order ?action ?target ?description ?inputVal ?waitVal
WHERE {
    ?task a cu:Task .
    ?task cu:hasStep ?step .
    ?step cu:stepOrder ?order .
    ?step cu:hasAction ?action .
    OPTIONAL { ?step cu:targetName ?target }
    OPTIONAL { ?step cu:stepDescription ?description }
    OPTIONAL { ?step cu:inputValue ?inputVal }
    OPTIONAL { ?step cu:waitDuration ?waitVal }
}
ORDER BY ?order
"""
```

After execution, step states are updated in the ontology and saved to a new file (`task_ontology_*_executed.owl`).

### Ontology Namespace

```turtle
@prefix cu: <http://example.org/computer-use#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
```

### Example: Step Representation in OWL

```xml
<cu:Step rdf:about="http://example.org/computer-use#Task_abc123_Step_1">
    <cu:stepOrder rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1</cu:stepOrder>
    <cu:hasAction rdf:resource="http://example.org/computer-use#open_application"/>
    <cu:targetName>Visual Studio</cu:targetName>
    <cu:stepDescription>Start Visual Studio</cu:stepDescription>
    <cu:expectedResult>Visual Studio is opened</cu:expectedResult>
    <cu:hasState rdf:resource="http://example.org/computer-use#PendingState"/>
</cu:Step>
```

## Prerequisites

### System Requirements

- Windows 10/11 (primary platform)
- Python 3.11 or higher
- Node.js 18 or higher
- FFmpeg installed and accessible in PATH

### Required API Keys

| Service        | Purpose                                         |
|----------------|-------------------------------------------------|
| Groq API       | LLM for instruction parsing and plan generation |
| OpenRouter API | Vision model for UI element detection           |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/StefaNNN772/Computer-Use-Video-Instructions.git
cd Computer-Use-Video-Instructions
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. FFmpeg Installation

**Windows (using winget):**
```bash
winget install FFmpeg
```

**Windows (using Chocolatey):**
```bash
choco install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory with the following content:

```env
# Required API Keys
GROQ_API_KEY=gsk_your_groq_api_key_here
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here

# Optional: FFmpeg paths (if not in system PATH)
SCREEN_RECORDER_DIRECT_PATH1=C:\ffmpeg\bin\ffmpeg.exe
SCREEN_RECORDER_DIRECT_PATH2=%USERPROFILE%\ffmpeg\bin\ffmpeg.exe
```

Create a `.env` file in the `frontend` directory with the following content:
```env
REACT_APP_SERVER_API_URL=http://localhost:5000
```

## Running the Application

### 1. Start the Backend Server

```bash
cd backend
python app.py
```

The Flask server will start on `http://localhost:5000`

### 2. Start the Frontend Development Server

```bash
cd frontend
npm start
```

The React application will open automatically on `http://localhost:3000`

### 3. Access the Application

Open your browser and navigate to `http://localhost:3000`

## Usage Guide

### Creating a Video Tutorial

1. **Enter Instruction**: Type a natural language instruction describing the tutorial you want to create. Examples:
   - "Create a C# console application in Visual Studio that prints Hello World"
   - "Open Chrome, navigate to YouTube, and search for Python tutorials"
   - "Create a new text file in Notepad with a greeting message"

2. **Generate Plan**: Click "Generate Plan" to create the execution plan. The system will:
   - Parse your instruction using LLM
   - Generate detailed steps
   - Create both JSON and OWL representations

3. **Review Plan**: Review the generated steps in the Task Plan Editor. You can:
   - Edit step descriptions
   - Modify target elements
   - Change action types
   - Add or remove steps

4. **Execute**: Click "Create Video" to execute the plan. The system will:
   - Minimize all windows
   - Read steps from the OWL ontology
   - Execute each step while recording the screen
   - Generate an MP4 video file

5. **View/Download**: Once completed, you can:
   - Play the video directly in the browser
   - Download the video file
   - View execution results

### Tutorial Library

Previously created tutorials are saved and can be accessed from the Tutorial Library section:
- View all saved tutorials with their goals
- Play videos directly
- Download video files
- Delete unwanted tutorials

## API Reference

### Endpoints

| Method | Endpoint                      | Description                              |
|--------|-------------------------------|------------------------------------------|
| GET    | `/api/health`                 | Health check                             |
| POST   | `/api/generate-plan`          | Generate execution plan from instruction |
| GET    | `/api/status/<job_id>`        | Get job status                           |
| GET    | `/api/task-plan/<job_id>`     | Get task plan                            |
| PUT    | `/api/task-plan/<job_id>`     | Update task plan                         |
| POST   | `/api/execute/<job_id>`       | Execute plan and record video            |
| POST   | `/api/regenerate/<job_id>`    | Regenerate video                         |
| GET    | `/api/owl/<job_id>`           | Get OWL file content and steps           |
| GET    | `/api/validate-plan/<job_id>` | Validate plan against ontology           |
| GET    | `/api/tutorials`              | List all saved tutorials                 |
| GET    | `/api/tutorials/<id>`         | Get specific tutorial                    |
| DELETE | `/api/tutorials/<id>`         | Delete tutorial                          |
| GET    | `/api/videos/<filename>`      | Stream video                             |
| GET    | `/api/download/<filename>`    | Download video                           |

### Example Request

```bash
curl -X POST http://localhost:5000/api/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Create a C# console application in Visual Studio"}'
```

### Example Response

```json
{
  "job_id": "abc12345",
  "status": "pending",
  "message": "Plan generation started"
}
```

## Project Structure

```
Computer-Use-Video-Instructions/
|-- backend/
|   |-- app.py                          # Flask application entry point
|   |-- requirements.txt                # Python dependencies
|   |-- .env                            # Environment variables (create this)
|   |-- ontology/
|   |   +-- computer_use.ttl            # Base OWL ontology (Turtle format)
|   |-- ontology_files/                 # Generated OWL files per task
|   |-- src/
|   |   |-- __init__.py
|   |   |-- models.py                   # Pydantic data models
|   |   |-- input_processor.py          # LLM instruction parsing
|   |   |-- task_decomposer.py          # LLM plan generation
|   |   |-- screen_recorder.py          # FFmpeg screen recording
|   |   |-- ontology/
|   |   |   |-- __init__.py
|   |   |   |-- ontology_manager.py     # RDFLib graph operations
|   |   |   |-- plan_mapper.py          # JSON to OWL mapping
|   |   |   |-- plan_validator.py       # Ontology-based validation
|   |   |   +-- ontology_executor.py    # SPARQL-based execution
|   |   +-- execution/
|   |       |-- __init__.py
|   |       |-- screen_analyzer.py      # Vision AI element detection
|   |       +-- action_performer.py     # PyAutoGUI actions
|   |-- videos/                         # Generated video files
|   +-- temp/                           # Task plan JSON files
|
|-- frontend/
|   |-- package.json
|   |-- tsconfig.json
|   |-- public/
|   |   +-- index.html
|   +-- src/
|       |-- index.tsx
|       |-- App.tsx
|       |-- App.css
|       |-- types/
|       |   +-- index.ts
|       +-- components/
|           |-- VideoRequestForm.tsx
|           |-- TaskPlanEditor.tsx
|           |-- VideoPlayer.tsx
|           |-- StatusIndicator.tsx
|           +-- TutorialLibrary.tsx
|
+-- README.md
```

## Technologies Used

### Backend

| Technology     | Version | Purpose                            |
|----------------|---------|------------------------------------|
| Python         | 3.11+   | Core programming language          |
| Flask          | 3.0     | Web framework for REST API         |
| Flask-CORS     | -       | Cross-origin resource sharing      |
| RDFLib         | -       | OWL/RDF parsing and SPARQL queries |
| Groq SDK       | -       | LLM API client                     |
| PyAutoGUI      | -       | GUI automation                     |
| Pillow         | -       | Image processing                   |
| Pydantic       | -       | Data validation                    |
| python-dotenv  | -       | Environment management             |

### Frontend

| Technology | Version | Purpose              |
|------------|---------|----------------------|
| React      | 18      | UI framework         |
| TypeScript | 4.9     | Type-safe JavaScript |
| Axios      | 1.6     | HTTP client          |

### External Services

| Service    | Model           | Purpose                              |
|------------|-----------------|--------------------------------------|
| Groq       | Llama 3.3 70B   | Instruction parsing, plan generation |
| OpenRouter | Qwen 2.5 VL 72B | Vision-based UI detection            |

### Tools

| Tool   | Purpose                             |
|--------|-------------------------------------|
| FFmpeg | Screen recording and video encoding |

## Limitations

1. **Platform**: Primarily designed for Windows. Limited support for Linux/macOS.

2. **Screen Resolution**: Best results with 1920x1080 or higher. Multi-monitor setups use primary display only.

3. **UI Detection**: Vision-based detection may fail for:
   - Non-standard UI frameworks
   - Rapidly changing interfaces
   - Low contrast elements
   - Non-English UI labels

4. **Tested Applications**:
   - Visual Studio 2022
   - VS Code
   - Chrome, Firefox, Opera, Edge
   - Notepad, Notepad++

5. **Execution Speed**: Includes delays between actions for reliability and video clarity.

6. **Error Recovery**: Limited automatic recovery from failed steps.

## License

This project was developed as part of a master's thesis on intelligent systems and modern educational technologies.
