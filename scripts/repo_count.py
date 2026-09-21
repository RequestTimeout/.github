import os
import requests

TOKEN = os.environ["ADMIN_PAT"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
private = 0
public = 0
page = 1

while True:
    response = requests.get(
        f"https://api.github.com/orgs/RequestTimeout/repos/?per_page=100&page={page}",
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()
    repos = response.json()
    if not repos:
        break
    for repo in repos:
        if repo["private"]:
            private += 1
        else:
            public += 1
    page += 1

print("Public:", public)
print("Private:", private)
