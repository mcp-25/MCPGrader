from dataclasses import dataclass

@dataclass
class GradeResult:
    name: str
    commit_hash: str
    status: dict[str, str]
    error: dict[str, str]
    stdout: dict[str, str]
    runtimes: dict[str, list[float]]
    data: dict[str, dict]

    def __avg_runtime(self, task_name: str) -> float:
        times = self.runtimes.get(task_name, [])
        if not times:
            return 0.0
        return sum(times) / len(times)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "commit_hash": self.commit_hash,
            "tasks": list(self.status.keys()),
            "status": self.status,
            "error": self.error,
            "stdout": self.stdout,
            "avg_runtime": {task: self.__avg_runtime(task) for task in self.runtimes},
            "data": self.data
        }
    
    def update_from_dict(self, info: dict, task_name: str) -> None:
        self.name = info.get("name", self.name)
        self.commit_hash = info.get("commit_hash", self.commit_hash)
        self.status[task_name] = info.get("status", self.status)
        self.error[task_name] = info.get("error", self.error)
        self.stdout[task_name] = info.get("stdout", self.stdout)
        self.runtimes[task_name] = info.get("runtimes", [])
        self.data[task_name] = info.get("data", self.data)