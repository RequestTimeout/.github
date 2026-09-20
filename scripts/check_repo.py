import os
import sys
import base64
import requests

TOKEN = os.environ["ADMIN_PAT"]

print("PAT exists:", bool(TOKEN))
print("PAT length:", len(TOKEN))

ORG = "RequestTimeout"

DEFAULT_LICENSE_URL = (
    "https://raw.githubusercontent.com/"
    "RequestTimeout/.github/main/profile/DEFAULT_LICENSE.md"
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_file(repo, path):
    response = requests.get(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        headers=HEADERS,
        timeout=15,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    data = response.json()

    if data.get("type") != "file":
        return None

    return base64.b64decode(data["content"])


def check_readme(repo):
    content = get_file(repo, "README.md")

    if content is None:
        return False, False

    text = content.decode("utf-8")

    return True, "__private__" in text


def check_license(repo, default_license):
    content = get_file(repo, "LICENSE.md")

    if content is None:
        return False

    return content == default_license


def check_codeowners(repo):
    paths = [
        "CODEOWNERS",
        ".github/CODEOWNERS",
        "docs/CODEOWNERS",
    ]

    content = None

    for path in paths:
        content = get_file(repo, path)

        if content is not None:
            break

    if content is None:
        return False

    owners = set()

    text = content.decode("utf-8")

    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split()

        if len(parts) >= 2:
            owners.update(parts[1:])

    owners = {
        owner.lstrip("@").lower()
        for owner in owners
    }

    return (
        "requesttimeout" in owners
        and len(owners) >= 2
    )


def set_visibility(repo, visibility):
    response = requests.patch(
        f"https://api.github.com/repos/{repo}",
        headers=HEADERS,
        json={"visibility": visibility},
        timeout=15,
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()


def get_repositories():
    repositories = []
    page = 1

    while True:
        response = requests.get(
            f"https://api.github.com/orgs/{ORG}/repos",
            headers=HEADERS,
            params={
                "per_page": 100,
                "page": page,
            },
            timeout=15,
        )

        response.raise_for_status()

        batch = response.json()

        if not batch:
            break

        repositories.extend(batch)
        page += 1

    return repositories


def check_repo(repo, default_license):
    print()
    print("=" * 60)
    print(f"Checking {repo}")

    readme_exists, private_marker = check_readme(repo)
    license_valid = check_license(repo, default_license)
    codeowners_valid = check_codeowners(repo)

    print("README:", readme_exists)
    print("LICENSE:", license_valid)
    print("CODEOWNERS:", codeowners_valid)
    print("__private__:", private_marker)

    requirements_met = (
        readme_exists
        and license_valid
        and codeowners_valid
    )

    if not requirements_met:
        print("Policy failed -> PRIVATE")
        set_visibility(repo, "private")
        return

    if private_marker:
        print("__private__ found -> PRIVATE")
        set_visibility(repo, "private")
    else:
        print("Policy passed -> PUBLIC")
        set_visibility(repo, "public")


def main():
    response = requests.get(
        DEFAULT_LICENSE_URL,
        timeout=15,
    )
    response.raise_for_status()

    default_license = response.content

    repositories = get_repositories()

    print(f"Found {len(repositories)} repositories.")

    for repository in repositories:
        check_repo(
            repository["full_name"],
            default_license,
        )


if __name__ == "__main__":
    main()
