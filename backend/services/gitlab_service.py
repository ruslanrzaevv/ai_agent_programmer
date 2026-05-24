import requests
from config import (
    GITLAB_TOKEN,
    GITLAB_PROJECT_ID,
    GITLAB_BASE_URL
)

headers = {
    "PRIVATE-TOKEN": GITLAB_TOKEN
}


def get_recent_commits():

    url = f"{GITLAB_BASE_URL}/projects/{GITLAB_PROJECT_ID}/repository/commits"

    response = requests.get(url, headers=headers)

    return response.json()


def create_branch(branch_name: str):

    url = f"{GITLAB_BASE_URL}/projects/{GITLAB_PROJECT_ID}/repository/branches"

    payload = {
        "branch": branch_name,
        "ref": "main"
    }

    response = requests.post(url, headers=headers, data=payload)

    return response.json()


def create_commit(
    branch: str,
    commit_message: str,
    file_path: str,
    content: str
):

    url = f"{GITLAB_BASE_URL}/projects/{GITLAB_PROJECT_ID}/repository/commits"

    payload = {
        "branch": branch,
        "commit_message": commit_message,
        "actions": [
            {
                "action": "update",
                "file_path": file_path,
                "content": content
            }
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    return response.json()


def create_merge_request(branch: str):

    url = f"{GITLAB_BASE_URL}/projects/{GITLAB_PROJECT_ID}/merge_requests"

    payload = {
        "source_branch": branch,
        "target_branch": "main",
        "title": "AI Generated Incident Fix"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    return response.json()