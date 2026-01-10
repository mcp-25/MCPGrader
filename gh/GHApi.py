import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .exceptions import GitHubException
from .structs import ClassroomInfo, AssignmentInfo, SubmissionInfo
from .filters import By
from typing import Iterator, Any, Optional


class GithubClassroomAPI:
    def __init__(self, token: str, timeout: int = 30, max_retries: int = 3) -> None:
        self.token = token
        self.base_url = "https://api.github.com"
        self.timeout = timeout
        self.session = self.__setup_request_session(max_retries)
    
    def __setup_request_session(self, max_retries: int) -> requests.Session:
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.0,  # Exponential backoff: 1s, 2s, 4s...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "TRACE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GithubClassroomAPI-Client <githubclassroomapi@francescodb.it>"
        })

        return session

    @staticmethod
    def __filter_checker(accepted_filters: set[By]):
        def decorator(func):
            def wrapper(self, by: By, value: str):
                if by not in accepted_filters:
                    raise ValueError(f"Invalid 'by' parameter. Accepted values are: {[f.value for f in accepted_filters]}")
                return func(self, by, value)
            return wrapper
        return decorator

    def __get_paginated_request(self, *paths: str) -> list:
        data = []
        page_idx = 1

        response = self.__get_request(*paths, query={"page": page_idx, "per_page": 50})
        data.extend(response)

        while response:
            page_idx += 1
            response = self.__get_request(*paths, query={"page": page_idx, "per_page": 50})
            data.extend(response)

        return data

    def __get_request(self, *paths: str, query: Optional[dict] = None) -> requests.Response:
        url = "/".join([self.base_url] + list(paths))
        try:
            response = self.session.get(url, params=query, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise GitHubException(f"Connection error while fetching {url}: {e}")
        except requests.exceptions.Timeout:
            raise GitHubException(f"Request to {url} timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise GitHubException(f"GET request to {url} failed with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise GitHubException(f"Request to {url} failed: {e}")

        return response.json()

    def list_classrooms(self) -> list[ClassroomInfo]:
        response = self.__get_paginated_request("classrooms")

        return [ClassroomInfo.from_dict(classroom) for classroom in response]

    @__filter_checker({By.ID, By.NAME, By.URL})
    def get_classroom_by(self, by: By, value: str) -> ClassroomInfo:
        classrooms = self.list_classrooms()

        for classroom in classrooms:
            if classroom.__getattribute__(by.value) == value:
                return classroom

        raise GitHubException(f"Classroom with {by.value} '{value}' not found.")

    @__filter_checker({By.ID, By.NAME, By.URL})
    def get_classrooms_by(self, by: By, value: str) -> Iterator[ClassroomInfo]:
        classrooms = self.list_classrooms()

        for classroom in classrooms:
            if classroom.__getattribute__(by.value) == value:
                yield classroom

        raise GitHubException(f"Classroom with {by.value} '{value}' not found.")

    def get_classroom_assignments(self, classroom_id: int) -> list[AssignmentInfo]:
        response = self.__get_paginated_request("classrooms", str(classroom_id), "assignments")

        return [AssignmentInfo.from_dict(assignment) for assignment in response]

    def get_submissions_for_assignment(self, assignment_id: int) -> list[SubmissionInfo]:
        response = self.__get_paginated_request("assignments", str(assignment_id), "accepted_assignments")

        return [SubmissionInfo.from_dict(submission) for submission in response]

    def get_assignment_by_id(self, assignment_id: int) -> AssignmentInfo:
        response = self.__get_request("assignments", str(assignment_id))

        return AssignmentInfo.from_dict(response)

    @__filter_checker({By.ID, By.TITLE, By.INVITE_LINK, By.SLUG})
    def get_assignment_by(self, by: By, value: Any) -> AssignmentInfo:
        if by == By.ID:
            return self.get_assignment_by_id(int(value))

        classrooms = self.list_classrooms()

        for classroom in classrooms:
            for assignment in self.get_classroom_assignments(classroom.id):
                if assignment.__getattribute__(by.value) == value:
                    return assignment

        raise GitHubException(f"Classroom with {by.value} '{value}' not found.")

    @__filter_checker({By.ID, By.TITLE, By.INVITE_LINK, By.SLUG})
    def get_assignments_by(self, by: By, value: str) -> Iterator[AssignmentInfo]:
        if by == By.ID:
            yield self.get_assignment_by_id(int(value))
            return

        classrooms = self.list_classrooms()

        for classroom in classrooms:
            for assignment in self.get_classroom_assignments(classroom.id):
                if assignment.__getattribute__(by.value) == value:
                    yield assignment

        raise GitHubException(f"Classroom with {by.value} '{value}' not found.")
