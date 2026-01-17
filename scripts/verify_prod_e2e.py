import requests
import time
import json
import sys
import uuid

# Configuration
API_URL = "https://iip-backend-7an2ps6yna-uc.a.run.app/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "X-User-ID": "e2e_tester_prod"
}

def log(step, message, status="INFO"):
    print(f"[{status}] {step}: {message}")

def check_response(response, context):
    if response.status_code >= 400:
        log(context, f"FAILED ({response.status_code}): {response.text}", "ERROR")
        sys.exit(1)
    return response.json()

def main():
    session_uid = str(uuid.uuid4())[:8]
    log("INIT", f"Starting E2E Test Session: {session_uid}")

    # 1. Create Team
    log("STEP 1", "Creating Project Team...")
    resp = requests.post(f"{API_URL}/teams", json={
        "teamname": f"Project Omega {session_uid}",
        "projectfocus": "Building a Feature Flagging System for GentleQuest"
    }, headers=HEADERS)
    team_data = check_response(resp, "Create Team")
    # TeamRead uses alias="teamid"
    team_id = team_data.get("teamid")
    log("STEP 1", f"Team Created. ID: {team_id}", "SUCCESS")

    # 2. Start Interview
    log("STEP 2", "Starting Interview Session...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/chat/start", headers=HEADERS)
    interview_data = check_response(resp, "Start Interview")
    # InterviewSession uses session_id (primary key, default alias usually same)
    interview_id = interview_data.get("session_id")
    log("STEP 2", f"Interview Started. ID: {interview_id}", "SUCCESS")

    # 3. Answer Questions (Simulated)
    answers = [
        "I want to decouple deployment from release to reduce risk.",
        "We use Python/FastAPI backend and Flutter frontend.",
        "It needs to support percentage-based rollouts and user-targeting."
    ]
    
    for i, answer in enumerate(answers):
        log(f"STEP 3.{i+1}", f"Answering: '{answer}'")
        resp = requests.post(f"{API_URL}/chat/{interview_id}/message", json={
            "content": answer
        }, headers=HEADERS)
        check_response(resp, f"Answer Question {i+1}")
        time.sleep(1) 

    # 4. Finalize Interview
    log("STEP 4", "Finalizing Interview & Extracting Insights...")
    resp = requests.post(f"{API_URL}/chat/{interview_id}/finalize", headers=HEADERS)
    check_response(resp, "Finalize Interview")
    log("STEP 4", "Interview Finalized.", "SUCCESS")
    
    # 5. Generate Personas
    log("STEP 5", "Generating Personas (AI)...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/personas/generate", headers=HEADERS)
    personas = check_response(resp, "Generate Personas")
    log("STEP 5", f"Generated {len(personas)} Personas.", "SUCCESS")

    # 6. Generate CVP
    log("STEP 6", "Generating CVP Canvas (AI)...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/cvp/generate", headers=HEADERS)
    cvp = check_response(resp, "Generate CVP")
    # CVPRead uses alias="valueproposition"
    val_prop = cvp.get("valueproposition", "")
    log("STEP 6", f"CVP Generated. Value Prop: {val_prop[:50]}...", "SUCCESS")

    # 7. Generate Roadmap
    log("STEP 7", "Generating Roadmap (AI)...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/roadmap/generate", headers=HEADERS)
    roadmap = check_response(resp, "Generate Roadmap")
    # MVPRoadmapRead uses alias="roadmap_id" (snake_case in alias!)
    # And features list
    features = roadmap.get("features", [])
    log("STEP 7", f"Roadmap Generated with {len(features)} features.", "SUCCESS")

    # 8. Generate Tasks
    log("STEP 8", "Generating Engineering Tasks (AI)...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/tasks/generate", headers=HEADERS)
    tasks = check_response(resp, "Generate Tasks")
    log("STEP 8", f"Generated {len(tasks)} Tasks.", "SUCCESS")
    if tasks:
         log("TASK_SAMPLE", f"Task 1: {tasks[0].get('title')}", "INFO")

    # 9. Project Brain Chat (RAG)
    log("STEP 9", "Testing Project Brain (RAG)...")
    # Start Project Chat Session
    resp = requests.post(f"{API_URL}/teams/{team_id}/project-chat/start", headers=HEADERS)
    proj_chat_data = check_response(resp, "Start Project Chat")
    proj_session_id = proj_chat_data.get("session_id")
    
    resp = requests.post(f"{API_URL}/teams/{team_id}/project-chat/{proj_session_id}/message", json={
        "content": "What is the complexity of the Admin UI feature?"
    }, headers=HEADERS)
    
    if resp.status_code == 200:
        answer = resp.json().get("content", "")
        log("STEP 9", f"Brain Answered: {answer[:100]}...", "SUCCESS")
    else:
         log("STEP 9", f"Brain Chat Failed: {resp.text}", "WARNING")

    log("DONE", "E2E Verification Complete. System is aligned and operational.", "SUCCESS")

if __name__ == "__main__":
    main()
