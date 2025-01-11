import requests

# GitHub API Token and Repo Info
GITHUB_TOKEN = "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"
REPO_OWNER = "colossusofNero"
REPO_NAME = "MetaGPT"

# Headers for authentication
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Function to create a new branch
def create_branch(branch_name, base_branch="main"):
    # Get the latest commit SHA from the base branch
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{base_branch}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching base branch: {response.json()}")
        return
    base_sha = response.json()["object"]["sha"]

    # Create the new branch
    branch_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs"
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }
    response = requests.post(branch_url, json=data, headers=HEADERS)
    if response.status_code == 201:
        print(f"Branch '{branch_name}' created successfully.")
    else:
        print(f"Error creating branch: {response.json()}")

# Example usage
create_branch("new-feature-branch")
