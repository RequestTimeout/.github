import os
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


def set_visibility(repo, visibility):
    response = requests.patch(
        f"https://api.github.com/repos/{repo}",
        headers=HEADERS,
        json={"visibility": visibility},
        timeout=15,
    )

    print("STATUS: ", response.status_code)
    
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

    print("README:", readme_exists)
    print("LICENSE:", license_valid)
    print("__private__:", private_marker)

    requirements_met = (
        readme_exists
        and license_valid
    )

    if not requirements_met:
        set_visibility(repo, "private")
        return

    if private_marker:
        set_visibility(repo, "private")
    else:
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
