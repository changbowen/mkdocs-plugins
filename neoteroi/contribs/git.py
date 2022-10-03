import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

from dateutil.parser import parse as parse_date

from neoteroi.contribs.domain import ContributionsReader, Contributor


class GitContributionsReader(ContributionsReader):

    _name_email_rx = re.compile(r"(?P<name>[\w\s]+)\s<(?P<email>[^\>]+)>")

    def _decode(self, value: bytes) -> str:
        try:
            return value.decode("utf8")
        except UnicodeDecodeError:
            return value.decode("ISO-8859-1")

    def _parse_name_and_email(self, name_and_email) -> Tuple[str, str]:
        match = self._name_email_rx.search(name_and_email)
        if match:
            name = match.groupdict()["name"]
            email = match.groupdict()["email"]
        else:
            name, email = ""
        return name, email

    def parse_committers(self, output: str) -> Iterable[Contributor]:
        for line in output.splitlines():
            count, name_and_email = line.split("\t")
            name, email = self._parse_name_and_email(name_and_email)
            yield Contributor(name, email, int(count))

    def get_contributors(self, file_path: Path) -> List[Contributor]:
        """
        Obtains the list of contributors for a file with the given path,
        using the Git CLI.
        """
        in_process = subprocess.Popen(
            ["git", "log", "--pretty=short"], stdout=subprocess.PIPE
        )
        result = self._decode(
            subprocess.check_output(
                [
                    "git",
                    "shortlog",
                    "--summary",
                    "--numbered",
                    "--email",
                    str(file_path),
                ],
                stdin=in_process.stdout,
            )
        )

        return list(self.parse_committers(result))

    def get_last_commit_date(self, file_path: Path) -> datetime:
        """Reads the last commit on a file."""
        result = self._decode(
            subprocess.check_output(
                ["git", "log", "-1", "--pretty=format:%ci", str(file_path)]
            )
        )
        return parse_date(result)