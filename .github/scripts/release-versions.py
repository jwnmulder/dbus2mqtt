#!/usr/bin/env python3
import json
import subprocess
import sys

from packaging import version


def get_versions_from_git_tags() -> list[version.Version]:
    result = subprocess.run(
        ["git", "tag"],
        capture_output=True, text=True, check=True
    )
    tags = result.stdout.strip().splitlines()
    versions = [t.lstrip("v") for t in tags if t.startswith("v")]

    parsed_versions = []
    for v in versions:
        try:
            parsed = version.parse(v)
            parsed_versions.append(parsed)
        except Exception as e:
            print(f"Error parsing version {v}: {e}")

    return parsed_versions

def latest_version_by_cycle(versions: list[version.Version], cycles: list[str]) -> dict[str, version.Version]:
    res = {}
    for cycle_str in cycles:
        cycle = version.parse(cycle_str)

        for v in versions:
            # check if version is in cycle range
            # cycle can be major or major.minor or major.minor.patch
            if len(v.release) > len(cycle.release) and v.base_version.startswith(cycle.base_version):
                # update if version is later within cycle
                if cycle not in cycles or v > cycle:
                    res[cycle_str] = v
    return res

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: release-versions.py 0.1 0.2 1.0 ...")
        sys.exit(1)

    versions = get_versions_from_git_tags()
    cycles = latest_version_by_cycle(versions, args)

    # Detect the overall latest version
    overall_latest = max(versions) if versions else None

    cycle_details = []
    for cycle in args:
        latest = cycles.get(cycle)
        if latest:
            cycle_details.append({
                "cycle": cycle,
                "latestVersion": latest.base_version,
                "isLatestStable": latest == overall_latest
            })

    print(json.dumps(cycle_details))

if __name__ == "__main__":
    main()
