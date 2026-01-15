import requests
import time
import json
import uuid
import sys

# Configuration
API_URL = "https://iip-backend-999376128638.us-central1.run.app/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "X-User-ID": "ghostdiary_stress_test"
}

def log(step, message):
    print(f"[{step}] {message}")

def check_response(resp, context):
    if resp.status_code >= 400:
        log("ERROR", f"{context} Failed: {resp.text}")
        sys.exit(1)
    return resp.json()

def main():
    session_uid = str(uuid.uuid4())[:8]
    team_name = f"GhostDiary Privacy {session_uid}"
    
    # 1. Create Team
    log("STEP 1", f"Creating Team: {team_name}")
    resp = requests.post(f"{API_URL}/teams", json={
        "teamname": team_name,
        "projectfocus": "An encrypted journal where data never leaves the local device, using CRDTs for multi-device sync."
    }, headers=HEADERS)
    team = check_response(resp, "Create Team")
    team_id = team['teamid']
    log("SUCCESS", f"Team Created: {team_id}")

    # 2. Start Interview
    log("STEP 2", "Starting Interview...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/chat/start", headers=HEADERS)
    session = check_response(resp, "Start Interview")
    session_id = session['session_id']
    log("SUCCESS", f"Interview Session: {session_id}")

    # 3. Conduct Interview (Simulated Answers)
    answers = [
        "We want a journaling app where the developer has zero access to user data. No cloud databases allowed. Sync must happen peer-to-peer.",
        "Encryption must be handled on-device before any sync occurs. We should use SQLite with WASM for local storage.",
        "The target audience is journalists and activists in repressive regimes."
    ]
    
    for i, ans in enumerate(answers):
        log(f"STEP 3.{i+1}", f"Answering: {ans[:50]}...")
        requests.post(f"{API_URL}/chat/{session_id}/message", json={"content": ans}, headers=HEADERS)
        time.sleep(1)

    # 4. Finalize
    log("STEP 4", "Finalizing Interview...")
    requests.post(f"{API_URL}/chat/{session_id}/finalize", headers=HEADERS)
    
    # 5. Generate Personas
    log("STEP 5", "Generating Personas...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/personas/generate", headers=HEADERS)
    personas = check_response(resp, "Generate Personas")
    log("SUCCESS", f"Generated {len(personas)} Personas: {[p['name'] for p in personas]}")

    # 6. Generate CVP
    log("STEP 6", "Generating CVP...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/cvp/generate", headers=HEADERS)
    cvp = check_response(resp, "Generate CVP")
    log("SUCCESS", f"CVP: {cvp.get('valueproposition', '')[:60]}...")

    # 7. Generate Roadmap
    log("STEP 7", "Generating Roadmap...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/roadmap/generate", headers=HEADERS)
    roadmap = check_response(resp, "Generate Roadmap")
    log("SUCCESS", f"Roadmap Features: {len(roadmap.get('features', []))}")

    # 8. Generate Tasks
    log("STEP 8", "Generating Tasks...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/tasks/generate", headers=HEADERS)
    tasks = check_response(resp, "Generate Tasks")
    log("SUCCESS", f"Generated {len(tasks)} Tasks")

    # 9. Query Brain
    log("STEP 9", "Querying Project Brain...")
    resp = requests.post(f"{API_URL}/teams/{team_id}/project-chat/start", headers=HEADERS)
    proj_session = check_response(resp, "Start Project Chat")
    proj_id = proj_session['session_id']
    
    query = "Does this project use a central cloud database?"
    log("QUERY", query)
    resp = requests.post(f"{API_URL}/teams/{team_id}/project-chat/{proj_id}/message", json={"content": query}, headers=HEADERS)
    answer = check_response(resp, "Query Brain")
    log("ANSWER", answer['content'])

    # Output JSON for blog
    output = {
        "persona": personas[0]['name'] if personas else "None",
        "cvp": cvp.get('valueproposition', ""),
        "roadmap_features": [f['feature_name'] for f in roadmap.get('features', [])],
        "brain_answer": answer['content']
    }
    with open("ghostdiary_results.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
