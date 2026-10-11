import os, requests, base64

TOKEN = os.environ['ADMIN_PAT']

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

page = 1
output = ""

while True:
    response = requests.get(
        "https://api.github.com/orgs/RequestTimeout/repos",
        headers=HEADERS,
        params={
            "type": "public",
            "per_page": 100,
            "page": page,
        },
        timeout=15
    )
    response.raise_for_status()
    repos = response.json()

    if not repos:
        break

    for repo in repos:
        if repo["private"]:
            continue

        name = repo["name"]
        branch = repo["default_branch"]

        diff_response = requests.get(
            f"https://api.github.com/repos/RequestTimeout/{name}/commits/{branch}",
            headers={
                **HEADERS,
                "Accept": "application/vnd.github.diff",
            },
            timeout=30
        )

        if diff_response.status_code != 200:
            continue

        diff = diff_response.text.strip()
        if not diff:
            continue

        output += f"# {name}\n```diff\n{diff}\n```\n"

    page += 1

path = "repos.md"

response = requests.get(
    f"https://api.github.com/repos/RequestTimeout/docs/contents/{path}",
    headers=HEADERS,
    params={"ref": "main"},
    timeout=15
)

data = {
    "message": "Update repository diffs",
    "content": base64.b64encode(output.encode()).decode(),
    "branch": "main"
}

if response.status_code == 200:
    data["sha"] = response.json()["sha"]
else:
    response.raise_for_status() if response.status_code != 404 else None

response = requests.put(
    f"https://api.github.com/repos/RequestTimeout/docs/contents/{path}",
    headers=HEADERS,
    json=data,
    timeout=30
)

response.raise_for_status()
