def greet(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        return "hello, agent"
    return f"hello, {cleaned}"


def main() -> int:
    print(greet("repo-context-map"))
    return 0
