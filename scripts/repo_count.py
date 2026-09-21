import os, requests, base64

TOKEN = os.environ['ADMIN_PAT']

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
        "https://api.github.com/orgs/RequestTimeout/repos",
        headers=HEADERS,
        params={
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
            private += 1
        else:
            public += 1
    page += 1

svg = \
f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="120" viewBox="0 0 360 120">
  <rect width="360" height="120" rx="10" fill="#0d1117" stroke="#30363d"/>

  <text x="24" y="30"
        fill="#f0f6fc"
        font-family="Arial, sans-serif"
        font-size="16"
        font-weight="700">Repositories:</text>

  <line x1="24" y1="42" x2="336" y2="42"
        stroke="#30363d"/>

  <text x="24" y="66"
        fill="#8b949e"
        font-family="Arial, sans-serif"
        font-size="14"
        font-weight="600">Public</text>

  <text x="24" y="98"
        fill="#f0f6fc"
        font-family="Arial, sans-serif"
        font-size="28"
        font-weight="700">{public}</text>

  <line x1="180" y1="52" x2="180" y2="106"
        stroke="#30363d"/>

  <text x="204" y="66"
        fill="#8b949e"
        font-family="Arial, sans-serif"
        font-size="14"
        font-weight="600">Private/in development</text>

  <text x="204" y="98"
        fill="#f0f6fc"
        font-family="Arial, sans-serif"
        font-size="28"
        font-weight="700">{private}</text>
</svg>
"""
response = requests.get(
    "https://api.github.com/repos/RequestTimeout/.github/contents/repos.svg",
    headers=HEADERS,
    params={"ref": "output"},
)

data = {
    "message": "Update repository count",
    "content": base64.b64encode(svg.encode()).decode(),
    "branch": "output"
}

if response.status_code == 200:
    data["sha"] = response.json()["sha"]

response = requests.put(
    "https://api.github.com/repos/RequestTimeout/.github/contents/repos.svg",
    headers=HEADERS,
    json=data
)

response.raise_for_status()
