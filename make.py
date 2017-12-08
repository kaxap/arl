import requests
import time

from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry

TABLE_DISCLAIMER = "## This is a most popular repository list for {lng} sorted by number of stars"
TABLE_HEADER = "|STARS|FORKS|ISSUES|NAME|DESCRIPTION|"
TABLE_SEPARATOR = "| --- | --- | --- | --- | --- |"
TABLE_ITEM_MASK = "| {n_stars} | {n_forks} | {n_issues} | [{name}]({url}) | {description} |"
MAX_PAGE = 10
URL_MASK = "https://api.github.com/search/repositories" \
           "?q=language:{lng}&sort=stars&order=desc&page={n_page}&per_page=100"

KEY_STAR_COUNT = "stargazers_count"
KEY_ISSUE_COUNT = "open_issues"
KEY_FORK_COUNT = "forks"
KEY_REPOSITORY_NAME = "name"
KEY_DESCRIPTION = "description"
KEY_URL = "html_url"
KEY_ITEMS = "items"

languages = ["Python", "Java", "C", "CPP", "SQL", "Node", "CSharp", "PHP", "Ruby", "TypeScript", "Swift", "ObjectiveC",
             "VB.net", "Assembly", "R", "Perl", "MATLAB", "Go", "Scala", "Groovy", "Lua", "Haskell", "CoffeeScript"]


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
                # obey rate limit
                if response.headers["X-RateLimit-Remaining"] == '0':
                    time_to_sleep = 1 + int(response.headers["X-RateLimit-Reset"]) - time.time()

                    if time_to_sleep > 0:
                        print(f"rate limit exceeded, sleeping ~{int(time_to_sleep)} seconds")
                        time.sleep(time_to_sleep)

                    return self.get_next(language, n_page)

                raise WrongReturnCodeException(response.text)
        finally:
            response.close()


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

    for n_page in range(1, MAX_PAGE + 1):
        data: dict = info_provider.get_next(language, n_page)
        for item in data[KEY_ITEMS]:
            result.append(TABLE_ITEM_MASK.format(n_stars=item.get(KEY_STAR_COUNT),
                                                 n_forks=item.get(KEY_FORK_COUNT),
                                                 n_issues=item.get(KEY_ISSUE_COUNT),
                                                 name=item.get(KEY_REPOSITORY_NAME),
                                                 url=item.get(KEY_URL),
                                                 description=item.get(KEY_DESCRIPTION)))

    return "\n".join(result)


if __name__ == "__main__":

    provider = RepositoryInformationProvider()
    for lng in languages:
        readme = generate_readme(lng, provider)
        with open(f"README-{lng}.md", "w", encoding="utf-8") as f:
            f.write(readme)
