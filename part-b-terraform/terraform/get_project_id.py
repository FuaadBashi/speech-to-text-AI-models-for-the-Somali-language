# get_project_id.py
import requests
import json
import sys

ACCESS_KEY = "DHAWLD4BCTYRLU61VB4R"
SECRET_KEY = "ND2Xv3V8XIPoJ0Mfdfe3cHAMuC6o9IBZm142JbX6"
IAM_ENDPOINT = "https://iam-apigateway-proxy.htgcloud-region-02.htgclouds.com"

# Step 1: Get a token using AK/SK
# HCS supports AK/SK token exchange
token_url = f"{IAM_ENDPOINT}/v3/auth/tokens"

payload = {
    "auth": {
        "identity": {
            "methods": ["hw_ak_sk"],
            "hw_ak_sk": {
                "access": {
                    "key": ACCESS_KEY
                },
                "secret": {
                    "key": SECRET_KEY
                }
            }
        }
    }
}

print("Requesting token from IAM...")
try:
    resp = requests.post(token_url, json=payload, verify=False, timeout=15)
    print(f"Status: {resp.status_code}")
    
    token = resp.headers.get("X-Subject-Token")
    if not token:
        print("No token in response. Full response:")
        print(resp.text[:2000])
        sys.exit(1)
    
    print(f"✅ Got token: {token[:20]}...")
    
    # Step 2: List projects
    projects_url = f"{IAM_ENDPOINT}/v3/projects"
    headers = {"X-Auth-Token": token}
    
    proj_resp = requests.get(projects_url, headers=headers, verify=False, timeout=15)
    print(f"\nProjects response ({proj_resp.status_code}):")
    
    data = proj_resp.json()
    projects = data.get("projects", [])
    
    if projects:
        print("\n✅ FOUND PROJECTS:")
        for p in projects:
            print(f"  Name: {p.get('name')}  |  ID: {p.get('id')}")
    else:
        print("Raw response:")
        print(json.dumps(data, indent=2)[:3000])

except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection failed: {e}")
    print("\nTrying alternate token method...")