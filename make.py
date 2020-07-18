# ﷽
import json
from typing import Optional

import requests
import time
import humanize
import datetime
import argparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry

from requests.structures import CaseInsensitiveDict

TABLE_DISCLAIMER = "## This is a most popular repository list for {lng} sorted by number of stars"
TABLE_HEADER = "|STARS|FORKS|ISSUES|LAST COMMIT|NAME/PLACE|DESCRIPTION|"
TABLE_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"
TABLE_ITEM_MASK = "| {n_stars} | {n_forks} | {n_issues} | {updated_at} | [{name}]({url})/{place} | {description} |"
MAX_PAGE = 10
URL_MASK = "https://api.github.com/search/repositories" \
           "?q=language:{lng}&sort=stars&order=desc&page={n_page}&per_page=100"
LAST_COMMIT_URL_MASK = "https://api.github.com/repos/{repo_full_name}/commits"

KEY_STAR_COUNT = "stargazers_count"
KEY_ISSUE_COUNT = "open_issues"
KEY_FORK_COUNT = "forks"
KEY_REPOSITORY_NAME = "name"
KEY_REPOSITORY_FULL_NAME = "full_name"
KEY_DESCRIPTION = "description"
KEY_URL = "html_url"
KEY_ITEMS = "items"
KEY_UPDATED_AT = 'updated_at'

languages = ["Verilog", "VHDL", "V", "Erlang", "Kotlin", "D", "Crystal", "Idris", "Python", "Java", "C", "CPP", "SQL",
             "Node", "CSharp", "PHP", "Ruby", "TypeScript", "Swift", "ObjectiveC",
             "VB.net", "Assembly", "R", "Perl", "MATLAB", "Go", "Scala", "Groovy", "Lua", "Haskell", "CoffeeScript",
             "Clojure", "Rust", "JavaScript", "ActionScript", "Elixir", "Elm", "PureScript"]


class WrongReturnCodeException(Exception):
    """
    HTTP exception class
    """
    pass


class RepositoryInformationProvider:
    session: requests.Session

    def __init__(self):
        self.session = requests.session()
        retry = Retry(total=30, connect=15, read=15, backoff_factor=5.0)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        with open("token.json", "r") as tf:
            token = json.load(tf)["token"]
        self.session.headers = {
            "Authorization": f"token {token}",
            "User-Agent": "Another Repository List",
        }

    @staticmethod
    def obey_rate_limit(headers: CaseInsensitiveDict) -> bool:
        if headers["X-RateLimit-Remaining"] == '0':
            time_to_sleep = 1 + int(headers["X-RateLimit-Reset"]) - time.time()

            if time_to_sleep > 0:
                print(f"rate limit exceeded, sleeping ~{int(time_to_sleep)} seconds")
                time.sleep(time_to_sleep)
            return True
        return False

    def get_next(self, language: str, n_page: int, request_timeout=20.0) -> dict:
        """
        retrieves information for a given language
        :param language: programming language (such as python or go)
        :param n_page: page number (starting from 1)
        :param request_timeout: HTTP request timeout in seconds
        :return: a dictionary with response from GitHub API
        """

        print(f"Requesting page #{n_page} for {language}")
        response = self.session.get(URL_MASK.format(n_page=n_page, lng=language), timeout=request_timeout)
        try:
            if response.ok:
                return response.json()
            else:
                # rate limiting?
                if self.obey_rate_limit(response.headers):
                    return self.get_next(language, n_page)

                raise WrongReturnCodeException(response.text)
        finally:
            response.close()

    def get_last_commit_date(self, repo_full_name: Optional[str]) -> Optional[str]:
        """
        returns last commit date for the given repo
        :param repo_full_name: repo full name, e.g. kaxap/arl or microsoft/TypeScript
        :return: last commit date in ISO format
        """
        if not repo_full_name:
            return None

        response = self.session.get(LAST_COMMIT_URL_MASK.format(repo_full_name=repo_full_name))
        try:
            if response.ok:
                return response.json()[0]["commit"]["author"]["date"]
            else:
                if self.obey_rate_limit(response.headers):
                    return self.get_last_commit_date(repo_full_name)
        except KeyError:
            return None
        finally:
            response.close()


def humanize_date(iso_date: str) -> str:
    if iso_date:
        return humanize.naturaltime(
            datetime.datetime.now() - datetime.datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ"))
    else:
        return "Unknown"


def generate_readme(language: str, info_provider: RepositoryInformationProvider) -> str:
    """
    generates a README markdown file with a table of most popular repositories for a given language
    :param language: programming language such as python or go
    :param info_provider: github repository info provider
    :return: text in markdown format
    """
    result = [TABLE_DISCLAIMER.format(lng=language),
              TABLE_HEADER,
              TABLE_SEPARATOR]

    place = 0
    for n_page in range(1, MAX_PAGE + 1):
        data: dict = info_provider.get_next(language, n_page)
        for i, item in enumerate(data[KEY_ITEMS]):
            last_commit_date = humanize_date(
                info_provider.get_last_commit_date(item.get(KEY_REPOSITORY_FULL_NAME, None)))
            place += 1

            desc = item.get(KEY_DESCRIPTION)
            if desc:
                desc = desc.replace("\n", " ")

            result.append(TABLE_ITEM_MASK.format(n_stars=item.get(KEY_STAR_COUNT),
                                                 n_forks=item.get(KEY_FORK_COUNT),
                                                 n_issues=item.get(KEY_ISSUE_COUNT),
                                                 name=item.get(KEY_REPOSITORY_NAME),
                                                 url=item.get(KEY_URL),
                                                 description=desc,
                                                 place=place,
                                                 updated_at=last_commit_date))
            print(f"{i + 1}/{len(data[KEY_ITEMS])}/{n_page}")

    return "\n".join(result)


if __name__ == "__main__":

    # parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--langs", type=str, help="comma-separated language names", default=",".join(languages))
    args = parser.parse_args()
    languages = [l.strip() for l in args.langs.split(",")]

    provider = RepositoryInformationProvider()
    for lng in languages:
        readme = generate_readme(lng, provider)
        with open(f"README-{lng}.md", "w", encoding="utf-8") as f:
            f.write(readme)
