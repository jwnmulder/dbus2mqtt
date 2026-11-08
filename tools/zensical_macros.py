from pathlib import Path


def define_env(env):
    @env.macro
    def include_readme():
        readme = Path("README.md").read_text(encoding="utf-8")

        return readme.replace(
            "https://jwnmulder.github.io/dbus2mqtt/",
            "",
        )
