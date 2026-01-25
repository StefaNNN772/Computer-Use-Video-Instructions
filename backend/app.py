import os
import json
import uuid
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from src.input_processor import InputProcessor
from src.task_decomposer import TaskDecomposer
from src. execution import Executor
from src.screen_recorder import ScreenRecorder

app = Flask(__name__)
CORS(app)

VIDEOS_DIR = os.path.abspath("videos")
TEMP_DIR = os.path.abspath("temp")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Job storage
jobs = {}


class JobStatus:
    PENDING = "pending"
    GENERATING_PLAN = "generating_plan"
    PLAN_READY = "plan_ready"
    EXECUTING = "executing"
    RECORDING = "recording"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


def save_task_plan(job_id: str, plan_dict: dict):
    plan_path = os.path.join(TEMP_DIR, f"task_plan_{job_id}.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan_dict, f, ensure_ascii=False, indent=2)
    return plan_path


def load_task_plan(job_id: str) -> dict:
    plan_path = os.path.join(TEMP_DIR, f"task_plan_{job_id}.json")
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_plan_task(job_id: str, instruction:  str):
    try:
        jobs[job_id]["status"] = JobStatus.GENERATING_PLAN
        jobs[job_id]["message"] = "Generating task plan"
        
        # Parsiranje instrukcije
        processor = InputProcessor()
        is_valid, message = processor.validate_input(instruction)
        
        if not is_valid:
            jobs[job_id]["status"] = JobStatus.FAILED
            jobs[job_id]["error"] = message
            return
        
        print(instruction)
        parsed = processor.parse(instruction)
        
        # Kreiranje plana
        decomposer = TaskDecomposer()
        plan = decomposer.decompose(parsed)
        
        plan_dict = {
            "original_instruction": plan.original_instruction,
            "goal": plan.goal,
            "prerequisites": plan.prerequisites,
            "steps": [
                {
                    "id": step.id,
                    "action": step.action. value,
                    "target": step.target,
                    "value": step.value,
                    "description": step.description,
                    "expected_result": step.expected_result
                }
                for step in plan.steps
            ],
            "success_criteria": plan.success_criteria
        }
        
        save_task_plan(job_id, plan_dict)
        
        jobs[job_id]["status"] = JobStatus.PLAN_READY
        jobs[job_id]["message"] = "Plan ready for review"
        jobs[job_id]["task_plan"] = plan_dict
        
    except Exception as e: 
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        print(f"[ERROR] generate_plan_task: {e}")
        import traceback
        traceback.print_exc()


def execute_plan_task(job_id: str):
    """Izvrsavanje plana, tj. snimanje"""
    try:
        jobs[job_id]["status"] = JobStatus.RECORDING
        jobs[job_id]["message"] = "Starting recording and execution"
        
        plan_dict = load_task_plan(job_id)
        if not plan_dict:
            jobs[job_id]["status"] = JobStatus.FAILED
            jobs[job_id]["error"] = "Plan not found"
            return
        
        # Privremeno cuvanje plana
        plan_path = os. path.join(TEMP_DIR, f"task_plan_{job_id}.json")
        
        # Executor za snimanje
        executor = Executor(slow_mode=True, verify_steps=False, record_video=True)
        
        # Postavljanje imena videa
        video_name = f"tutorial_{job_id}"
        
        # Izvrsavanje
        jobs[job_id]["status"] = JobStatus.EXECUTING
        jobs[job_id]["message"] = "Executing steps"
        
        results = executor.execute_from_json(plan_path, video_name=video_name)
        
        video_path = results.get("video_path")
        
        if video_path and os.path.exists(video_path):
            # Premjestanje videa u videos folder ukoliko nije tamo
            video_filename = os.path.basename(video_path)
            final_video_path = os.path.join(VIDEOS_DIR, video_filename)
            
            if video_path != final_video_path:
                import shutil
                shutil.move(video_path, final_video_path)
                video_path = final_video_path
            
            jobs[job_id]["status"] = JobStatus.COMPLETED
            jobs[job_id]["message"] = "Video successfully created!"
            jobs[job_id]["video_filename"] = os.path.basename(video_path)
            jobs[job_id]["video_url"] = f"/api/videos/{os.path.basename(video_path)}"
            jobs[job_id]["results"] = {
                "successful_steps": results.get("successful_steps", 0),
                "failed_steps": results.get("failed_steps", 0),
                "total_steps": results.get("total_steps", 0)
            }
        else:
            jobs[job_id]["status"] = JobStatus. FAILED
            jobs[job_id]["error"] = "Video not created"
            
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        print(f"[ERROR] execute_plan_task: {e}")
        import traceback
        traceback.print_exc()


# -------------------- API Endpoints --------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime. now().isoformat()
    })


@app.route("/api/generate-plan", methods=["POST"])
def generate_plan():
    """
    Generisanje plana iz instrukcije
    
    Request:
        {"instruction": "Create C# instruction..."}
    
    Response:
        {"job_id": "xxx", "status": "pending"}
    """
    data = request.get_json()
    
    if not data or "instruction" not in data:
        return jsonify({"error": "Missing 'instruction' field"}), 400
    
    instruction = data["instruction"]. strip()
    
    if len(instruction) < 10:
        return jsonify({"error": "Instruction is too short"}), 400
    
    # Kreira se job ID sa jedinstvvenim ID-em
    job_id = str(uuid.uuid4())[:8]
    
    jobs[job_id] = {
        "id": job_id,
        "instruction": instruction,
        "status":  JobStatus.PENDING,
        "message": "Job created",
        "created_at": datetime.now().isoformat(),
        "task_plan": None,
        "video_url": None,
        "error": None
    }
    
    # Pokrece se pozadinsko izvrsavanje
    thread = threading.Thread(
        target=generate_plan_task,
        args=(job_id, instruction)
    )
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status":  JobStatus.PENDING,
        "message": "Plan generation started"
    })


@app.route("/api/execute/<job_id>", methods=["POST"])
def execute_plan_endpoint(job_id:  str):
    """
    Izvrsavanje plana i snimanje videa
    """
    if job_id not in jobs: 
        return jsonify({"error":  "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] not in [JobStatus.PLAN_READY, JobStatus. COMPLETED]:
        return jsonify({"error": f"Plan not ready (status: {job['status']})"}), 400
    
    # Pozadinsko izvrsavanje plana
    thread = threading. Thread(
        target=execute_plan_task,
        args=(job_id,)
    )
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status": JobStatus.RECORDING,
        "message": "Execution started"
    })


@app.route("/api/status/<job_id>", methods=["GET"])
def get_status(job_id: str):
    """Vracanje koji je status job-a"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    return jsonify({
        "id": job["id"],
        "status": job["status"],
        "message": job. get("message", ""),
        "instruction": job.get("instruction", ""),
        "task_plan": job.get("task_plan"),
        "video_url": job.get("video_url"),
        "video_filename": job.get("video_filename"),
        "results":  job.get("results"),
        "error": job.get("error"),
        "created_at": job.get("created_at")
    })


@app.route("/api/task-plan/<job_id>", methods=["GET"])
def get_task_plan(job_id: str):
    """Prikazivanje task plana za trazeni job ID"""
    if job_id not in jobs: 
        return jsonify({"error": "Job not found"}), 404
    
    plan = load_task_plan(job_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    
    return jsonify(plan)


@app.route("/api/task-plan/<job_id>", methods=["PUT"])
def update_task_plan(job_id: str):
    """Azuriranje task plana"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    data = request.get_json()
    
    if not data: 
        return jsonify({"error": "Nedostaje task plan"}), 400
    
    save_task_plan(job_id, data)
    jobs[job_id]["task_plan"] = data
    jobs[job_id]["status"] = JobStatus.PLAN_READY
    jobs[job_id]["message"] = "Plan updated"
    
    return jsonify({
        "success": True,
        "message":  "Plan successfully updated"
    })


@app.route("/api/regenerate/<job_id>", methods=["POST"])
def regenerate_video(job_id: str):
    """Regenerisanje video upustva za azurirani task plan ili vec postojeci task plan"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    old_video = jobs[job_id]. get("video_filename")
    if old_video:
        old_path = os.path.join(VIDEOS_DIR, old_video)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
    
    # Postavljanje novog statusa job-a
    jobs[job_id]["video_url"] = None
    jobs[job_id]["video_filename"] = None
    jobs[job_id]["results"] = None
    jobs[job_id]["error"] = None
    
    thread = threading. Thread(
        target=execute_plan_task,
        args=(job_id,)
    )
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status": JobStatus.RECORDING,
        "message": "Regeneration started"
    })


@app.route("/api/videos/<filename>", methods=["GET"])
def get_video(filename: str):
    """Postavljanje video upustva"""
    return send_from_directory(VIDEOS_DIR, filename)


@app.route("/api/download/<filename>", methods=["GET"])
def download_video(filename: str):
    """Preuzimanje video upustva"""
    file_path = os.path.join(VIDEOS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    """Lista svih job-ova"""
    return jsonify({
        "jobs": list(jobs.values())
    })


if __name__ == "__main__": 
    print("\n" + "=" * 60)
    print("   VIDEO TUTORIAL GENERATOR - Flask Backend")
    print("=" * 60)
    print(f"   Videos:  {VIDEOS_DIR}")
    print(f"   Temp:  {TEMP_DIR}")
    print("=" * 60)
    print("\n   Starting on http://localhost:5000\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)