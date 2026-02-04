import logging
import os
from github import Github
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
github = Github(GITHUB_TOKEN)


def query_github(query_type: str, repository: str) -> str:
    """
    Fetches the real time data from Github repository
    query_type : The type of information needed from the github repository (commits, messages,project overview)
    repository : The name of the repository
    """
    repo = github.get_repo(repository)
    commits = repo.get_commits()[:2]
    messages = []
    for c in commits:
        messages.append(c.commit.message)
    read_me = fetch_readme(repository)
    return messages


def fetch_readme(repo_name: str):
    """
    
    """
    repo = github.get_repo(repo_name)
    return repo.get_readme().decoded_content.decode("utf-8")


if __name__ == "__main__":
    print(query_github("Abhijithsai451/realtime_threat_detection_multi_agent"))
