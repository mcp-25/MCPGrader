from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import List, Optional, Any
import hashlib
import os
from os import path

@dataclass_json
@dataclass
class AssignmentTaskConfig:
    name: str
    test_script_path: str
    slurm_backend: SlurmBackendConfig
    skip: bool = False
    blocking: bool = False

    def assert_valid(self) -> None:
        assert isinstance(self.name, str) and self.name, "name must be a non-empty string"
        assert self.test_script_path, "test_script_path must be provided"
        assert os.path.exists(self.test_script_path), f"test_script_path {self.test_script_path} does not exist"
        self.slurm_backend.assert_valid()
        assert isinstance(self.skip, bool), "skip must be a boolean"
        assert isinstance(self.blocking, bool), "blocking must be a boolean"


@dataclass_json
@dataclass
class AssignmentConfig:
    name: str
    invite_link: Optional[str] = None
    slug: Optional[str] = None
    id: Optional[int] = None
    preserve_repo_files: bool = False
    tasks: List[AssignmentTaskConfig] = None


    def assert_valid(self) -> None:
        assert isinstance(self.name, str) and self.name, "name must be a non-empty string"
        assert any([self.invite_link, self.slug, self.id]), "at least one of invite_link, slug, or id must be provided"
        assert isinstance(self.preserve_repo_files, bool), "preserve_repo_files must be a boolean"
        assert isinstance(self.tasks, list) and self.tasks, "tasks must be a non-empty list"
        for task in self.tasks:
            task.assert_valid()

        # assert no duplicate task names
        task_names = [task.name for task in self.tasks]
        assert len(task_names) == len(set(task_names)), f"Duplicate task names found in assignment {self.name}"

@dataclass_json
@dataclass
class SlurmBackendConfig:
    config: dict[str, Any] = None

    def assert_valid(self) -> None:
        assert isinstance(self.config, dict), "config must be a dictionary"

@dataclass_json
@dataclass
class GraderConfig:
    working_dir: str
    grades_file: str
    github_pat: Optional[str] = None

    def assert_valid(self) -> None:
        assert isinstance(self.working_dir, str) and self.working_dir, "working_dir must be a non-empty string"
        assert path.exists(self.working_dir), f"working_dir {self.working_dir} does not exist"
        assert isinstance(self.grades_file, str) and self.grades_file, "grades_file must be a non-empty string"

@dataclass_json
@dataclass
class ProgramConfig:
    grader: GraderConfig
    assignments: List[AssignmentConfig]

    def assert_valid(self) -> None:
        for assignment in self.assignments:
            assignment.assert_valid()

        # assert no duplicate assignment names
        assignment_names = [assignment.name for assignment in self.assignments]
        assert len(assignment_names) == len(set(assignment_names)), "Duplicate assignment names found"

        self.grader.assert_valid()