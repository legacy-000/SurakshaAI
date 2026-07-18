from functions.auth.rbac_middleware import RBACMiddleware
from models.dto import UserContextDTO


def test_investigator_can_view_sql():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Test",
                          email="t@t.com", role_id=1, role_name="Investigator")
    scope = rbac.get_authorization_scope(user)
    assert scope.can_view_sql


def test_analyst_cannot_view_pii():
    rbac = RBACMiddleware()
    user = UserContextDTO(user_id="ANL001", kgid="ANL001", first_name="Test",
                          email="t@t.com", role_id=2, role_name="Analyst")
    scope = rbac.get_authorization_scope(user)
    assert not scope.can_view_pii
