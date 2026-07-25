"""Territory access control: officers must only see their own jurisdiction."""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8077"

USERS = {
    "dgp":       {"role": "dgp", "district": "State HQ", "range": ""},
    "sp_mysuru": {"role": "sp", "district": "Mysuru", "range": "Mysuru"},
    "sp_blr":    {"role": "sp", "district": "Bengaluru City", "range": "Bengaluru"},
    "dig_mysuru": {"role": "dig", "district": "Mysuru", "range": "Mysuru"},
    "constable": {"role": "constable", "district": "Bengaluru City", "range": "Bengaluru"},
}


def get(path, who):
    u = USERS[who]
    req = urllib.request.Request(BASE + path, headers={
        "X-User-Id": "1", "X-User-Name": who, "X-User-Role": u["role"],
        "X-User-District": u["district"], "X-User-Range": u["range"]})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:120]


failed = 0


def check(label, cond, detail=""):
    global failed
    failed += not cond
    print(f"[{'ok' if cond else 'FAIL'}] {label}{('  ' + detail) if detail else ''}")


print("=== case listing scoped by territory ===")
_, dgp = get("/api/cases?limit=500", "dgp")
_, mys = get("/api/cases?limit=500", "sp_mysuru")
_, blr = get("/api/cases?limit=500", "sp_blr")
print(f"    dgp={dgp['total']}  sp_mysuru={mys['total']}  sp_blr={blr['total']}")
check("DGP sees state-wide", dgp["total"] > 0)
check("SP Mysuru sees fewer than DGP", mys["total"] < dgp["total"])
check("SP Mysuru sees only Mysuru",
      {c["district"] for c in mys["items"]} <= {"Mysuru"},
      str({c["district"] for c in mys["items"]}))
check("SP Bengaluru sees only Bengaluru City",
      {c["district"] for c in blr["items"]} <= {"Bengaluru City"},
      str({c["district"] for c in blr["items"]}))
check("two SPs see different case sets",
      {c["id"] for c in mys["items"]} & {c["id"] for c in blr["items"]} == set())

print("\n=== range scope (DIG Mysuru covers whole range) ===")
_, dig = get("/api/cases?limit=500", "dig_mysuru")
dig_d = {c["district"] for c in dig["items"]}
print(f"    dig sees districts: {sorted(dig_d)}")
check("DIG sees >= own district", dig["total"] >= mys["total"])
check("DIG still not state-wide", dig["total"] < dgp["total"])

print("\n=== direct case access outside territory (IDOR) ===")
foreign = next((c for c in dgp["items"] if c["district"] != "Mysuru"), None)
code, _ = get(f"/api/cases/{foreign['id']}", "sp_mysuru")
check("out-of-territory case detail -> 404", code == 404, f"got {code}")
own = next((c for c in mys["items"]), None)
code, _ = get(f"/api/cases/{own['id']}", "sp_mysuru")
check("own case detail -> 200", code == 200, f"got {code}")

print("\n=== filters must not leak other districts ===")
_, f_mys = get("/api/cases/filters", "sp_mysuru")
check("filters list only own district", set(f_mys["districts"]) <= {"Mysuru"},
      str(f_mys["districts"]))

print("\n=== victims scoped ===")
_, v_dgp = get("/api/victims/list", "dgp")
_, v_mys = get("/api/victims/list", "sp_mysuru")
print(f"    dgp victims={v_dgp['total']}  sp_mysuru victims={v_mys['total']}")
check("SP sees fewer victims than DGP", v_mys["total"] < v_dgp["total"])
check("victims listed are all in territory",
      {x.get("district") for x in v_mys["victims"]} <= {"Mysuru"},
      str({x.get("district") for x in v_mys["victims"]}))

print("\n=== socio aggregates scoped ===")
_, s_dgp = get("/api/socio/gender", "dgp")
_, s_mys = get("/api/socio/gender", "sp_mysuru")
t_dgp = sum(x["value"] for x in s_dgp)
t_mys = sum(x["value"] for x in s_mys)
print(f"    dgp accused={t_dgp}  sp_mysuru accused={t_mys}")
check("socio totals scoped", t_mys < t_dgp)

print("\n=== financial scoped (via case/accused joins) ===")
_, fd = get("/api/financial/summary", "dgp")
_, fm = get("/api/financial/summary", "sp_mysuru")
print(f"    dgp txns={fd['total_transactions']} loss={fd['financial_loss']:.0f} "
      f"susp={fd['suspicious_accounts']}")
print(f"    mys txns={fm['total_transactions']} loss={fm['financial_loss']:.0f} "
      f"susp={fm['suspicious_accounts']}")
check("transactions scoped", fm["total_transactions"] < fd["total_transactions"])
check("financial loss scoped", fm["financial_loss"] < fd["financial_loss"])
check("suspicious accounts scoped",
      fm["suspicious_accounts"] < fd["suspicious_accounts"])

_, gd = get("/api/financial/graph", "dgp")
_, gm = get("/api/financial/graph", "sp_mysuru")
print(f"    graph edges dgp={len(gd['edges'])} mys={len(gm['edges'])}")
check("money graph scoped", len(gm["edges"]) < len(gd["edges"]))

# every edge in the scoped graph must belong to a case the officer can open
_, mys_cases = get("/api/cases?limit=500", "sp_mysuru")
own_ids = {str(c["id"]) for c in mys_cases["items"]}
stray = [e for e in gm["edges"] if str(e.get("case_id")) not in own_ids]
check("no graph edge outside territory", not stray,
      f"{len(stray)} stray edges" if stray else "")

_, sd = get("/api/financial/suspicious-accounts", "dgp")
_, sm = get("/api/financial/suspicious-accounts", "sp_mysuru")
print(f"    suspicious accounts dgp={len(sd)} mys={len(sm)}")
check("suspicious account list scoped", len(sm) < len(sd))

print("\n" + ("ALL PASS" if not failed else f"{failed} FAILED"))
sys.exit(1 if failed else 0)
