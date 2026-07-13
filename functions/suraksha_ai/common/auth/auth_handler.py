from models.dto import LoginRequestDTO, UserContextDTO


class AuthHandler:
    def __init__(self):
        self._users = {}

    def login(self, req: LoginRequestDTO) -> dict:
        if not req.kgid or not req.password:
            return {"error": "AUTH_001", "message": "Invalid KGID or password."}
        role_map = {"INV001": ("Investigator", 1), "ANL001": ("Analyst", 2),
                    "SUP001": ("Supervisor", 3), "POL001": ("Policymaker", 4),
                    "ADM001": ("System Administrator", 5)}
        role_name, role_id = role_map.get(req.kgid.upper(), ("Investigator", 1))
        return {
            "token": f"mock_jwt_{req.kgid}_1",
            "user": {"user_id": req.kgid, "kgid": req.kgid,
                     "first_name": req.kgid, "role_id": role_id,
                     "role_name": role_name, "unit_id": 1, "district_id": 1},
            "expires_in": 3600
        }
