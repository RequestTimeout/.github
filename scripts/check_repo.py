import os
import sys
import requests

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["ADMIN_PAT"]

DEFAULT_LICENSE_URL = (
    "https://raw.githubusercontent.com/"
    "RequestTimeout/.github/main/profile/DEFAULT_LICENSE.md"
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def check_readme():
    if not os.path.isfile("README.md"):
        return False, False

    with open("README.md", "r", encoding="utf-8") as file:
        content = file.read()

    return True, "__private__" in content


def check_license():
    if not os.path.isfile("LICENSE.md"):
        return False

    with open("LICENSE.md", "rb") as file:
        local_license = file.read()

    response = requests.get(DEFAULT_LICENSE_URL, timeout=15)
    response.raise_for_status()

    return local_license == response.content


def check_codeowners():
    paths = [
        "CODEOWNERS",
        ".github/CODEOWNERS",
        "docs/CODEOWNERS",
    ]

    path = next((p for p in paths if os.path.isfile(p)), None)

    if path is None:
        return False

    owners = set()

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
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


def set_visibility(visibility):
    response = requests.patch(
        f"https://api.github.com/repos/{REPO}",
        headers=HEADERS,
        json={"visibility": visibility},
        timeout=15,
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()


def main():
    readme_exists, private_marker = check_readme()
    license_valid = check_license()
    codeowners_valid = check_codeowners()

    requirements_met = (
        readme_exists
        and license_valid
        and codeowners_valid
    )

    if not requirements_met:
        set_visibility("private")
        sys.exit(1)

    if private_marker:
        set_visibility("private")
    else:
        set_visibility("public")


if __name__ == "__main__":
    main()
