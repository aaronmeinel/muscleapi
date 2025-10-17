from src.protocols import Repository


class PlanManagementService:
    repository: Repository

    def __init__(self, repository: Repository):
        self.repository = repository

    def create_template(self, name: str, exercises: list[str]):
        self.repository.add({"name": name, "exercises": exercises})

    def get_plan(self, name: str):
        pass

    def list_plans(self):
        pass

    def list_exercises(self):
        pass
