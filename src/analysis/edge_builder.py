import json

class EdgeBuilder:
    def __init__(self, issues_path="data/issues.json", pulls_path="data/pulls.json"):
        self.issues = json.load(open(issues_path, encoding="utf-8"))
        self.pulls = json.load(open(pulls_path, encoding="utf-8"))

    def build_edges(self):
        edges = []
        for issue in self.issues:
            if "user" in issue and issue.get("comments", 0) > 0:
                user = issue["user"]["login"]
                for comment in issue.get("comments", []):
                    if "user" in comment:
                        edges.append((user, comment["user"]["login"], 2))
        for pr in self.pulls:
            if "user" in pr:
                user = pr["user"]["login"]
                if "merged_by" in pr and pr["merged_by"]:
                    edges.append((user, pr["merged_by"]["login"], 5))
        return edges
