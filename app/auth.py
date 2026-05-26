def login(username: str, password: str) -> bool:
    if not username or not password:
        return False
    return username == "demo" and password == "password"