r"""
StreamSync ML Engine — Full Test Suite
Run from repo root:  .venv\Scripts\python.exe -X utf8 backend\test_all_models.py
"""
import sys, os, asyncio, json, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
CYAN   = "\033[96m"; BOLD = "\033[1m"; RESET = "\033[0m"
PASS = f"{GREEN}[PASS]{RESET}"; FAIL = f"{RED}[FAIL]{RESET}"

passed = failed = 0

def ok(label, detail=""):
    global passed; passed += 1
    print(f"  {PASS}  {label}" + (f"  --> {detail}" if detail else ""))

def fail(label, detail=""):
    global failed; failed += 1
    print(f"  {FAIL}  {label}" + (f"  --> {detail}" if detail else ""))

def section(title):
    sep = "-" * 60
    print(f"\n{BOLD}{CYAN}{sep}\n {title}\n{sep}{RESET}")


# ============================================================
# SETUP
# ============================================================
section("SETUP")
try:
    from db.mock_db import generate_mock_products
    from db.redis_client import get_redis_sync
    generate_mock_products()
    redis_sync = get_redis_sync()
    ok("Mock DB seeded (20 products)")
except Exception as e:
    fail("Mock DB seed", str(e)); sys.exit(1)


# ============================================================
# MODEL 1 — PRICING MODEL
# ============================================================
section("MODEL 1 · Pricing Model (Demand-Elasticity)")
try:
    from engine.pricing_model import calculate_new_price, calculate_confidence
    base = cur = 100_000.0

    p = calculate_new_price(base, cur, 85, 40)
    ok("High velocity (85) raises price", f"{cur:.0f} -> {p:.0f}") if p > cur else fail("High velocity should raise price", str(p))

    p = calculate_new_price(base, cur, 15, 2)
    ok("Low velocity (15) lowers price",  f"{cur:.0f} -> {p:.0f}") if p < cur else fail("Low velocity should lower price",  str(p))

    p = calculate_new_price(base, cur, 50, 10)
    ok("Mid velocity (50) minor noise",   f"delta={abs(p-cur):.0f}") if abs(p-cur) < cur*0.05 else fail("Mid too large", str(p))

    p = calculate_new_price(base, base*1.48, 100, 100)
    ok("Guardrail cap <=150% base enforced", str(p)) if p <= base*1.50 else fail("Guardrail violated", str(p))

    c = calculate_confidence(80, 30)
    ok("Confidence in [0,1]", str(c)) if 0 <= c <= 1 else fail("Confidence out of range", str(c))

except Exception as e:
    fail("Pricing model crashed", str(e))


# ============================================================
# MODEL 2 — SEMANTIC SEARCH
# ============================================================
section("MODEL 2 · Semantic Search Engine (TF-IDF + Attribute Boost)")
try:
    from engine.semantic_search import semantic_engine, SemanticSearchEngine
    semantic_engine.build_index_from_redis_sync(redis_sync)

    ok(f"Index built", f"{len(semantic_engine._products)} products / {len(semantic_engine._idf)} terms") \
        if semantic_engine._ready else fail("Index not ready")

    cases = [
        ("green mat",           "Yoga",      "colors",     "green"),
        ("wireless earbuds",    "Buds",      None,         None),
        ("leather bag",         "Backpack",  None,         None),
        ("blue foam roller",    "Foam",      "colors",     "blue"),
    ]
    for query, expect_substr, attr_key, attr_val in cases:
        r = semantic_engine.query(query, limit=5)
        names = [p['name'] for p in r['products']]
        hit = any(expect_substr in n for n in names)
        ok(f'"{query}" -> found "{expect_substr}"', str(names[:2])) if hit else fail(f'"{query}" expected "{expect_substr}"', str(names))
        if attr_key:
            parsed = r['query_parsed']
            found = attr_val in parsed.get(attr_key, [])
            ok(f'  Attribute "{attr_key}"="{attr_val}" extracted') if found else fail(f'  Attribute "{attr_key}" not extracted', str(parsed))
        if r['products']:
            ok("  matchScore present", str(r['products'][0].get('matchScore'))) if 'matchScore' in r['products'][0] else fail("  matchScore missing")

    cold = SemanticSearchEngine()
    cr = cold.query("shoes", 5)
    ok("Cold-start returns status='cold'") if cr['status'] == 'cold' else fail("Cold-start not safe", str(cr.get('status')))

except Exception as e:
    import traceback; fail("Semantic search crashed", traceback.format_exc(limit=2))


# ============================================================
# MODEL 3 — RECOMMENDATION ENGINE
# ============================================================
section("MODEL 3 · Recommendation Engine (Item-Item Collaborative Filtering)")

async def test_rec():
    from db.redis_client import get_redis_async
    import engine.recommendation_engine as rec
    r = get_redis_async()

    for sess in ["sess_T1", "sess_T2", "sess_T3"]:
        await rec.record_click(r, "prod-1", sess)
        await rec.record_click(r, "prod-5", sess)

    recs1 = await rec.get_recommendations(r, "prod-1", "sess_X", limit=4)
    recs5 = await rec.get_recommendations(r, "prod-5", "sess_Y", limit=4)

    ok("prod-1 recommends prod-5 (co-clicked)", str(recs1)) if "prod-5" in recs1 else fail("Co-click not in recs", str(recs1))
    ok("prod-5 recommends prod-1 (symmetric)",  str(recs5)) if "prod-1" in recs5 else fail("Symmetry missing",    str(recs5))

    recs_cold = await rec.get_recommendations(r, "prod-99", "sess_Z", limit=4)
    ok("Cold-start fallback returns results", str(recs_cold)) if recs_cold else fail("Cold-start empty")

    hist = await r.smembers("session:sess_T1:clicks")
    ok("Session history in Redis", str(hist)) if "prod-1" in hist else fail("Session history missing", str(hist))

asyncio.run(test_rec())


# ============================================================
# MODEL 4 — PERSONALISATION ENGINE
# ============================================================
section("MODEL 4 · Personalisation Engine (Session Interest Vectors)")

async def test_pers():
    from db.redis_client import get_redis_async
    import engine.personalisation_engine as pers
    r = get_redis_async()
    sid = "test_pers_42"

    # prod-1=Electronics, prod-2=Apparel, prod-3=Home (categories cycle per index)
    # VIEW = +1.0 each, ADD_TO_CART = +3.0
    # prod-1 (VIEW +1) + prod-7 (Electronics VIEW +1) + prod-13 (Electronics VIEW +1) + prod-1 ADD_TO_CART (+3) = 6.0
    for pid in ["prod-1", "prod-7", "prod-13"]:   # all Electronics (index 0,6,12)
        await pers.update_session(r, sid, pid, "VIEW")
    await pers.update_session(r, sid, "prod-1", "ADD_TO_CART")  # +3.0

    profile = await pers.get_session_profile(r, sid)
    elec = profile.get("Electronics", 0)
    ok("Electronics interest >= 5.0 accumulated", f"score={elec}") if elec >= 5.0 else fail("Interest not accumulated", str(profile))

    mixed = ["prod-5", "prod-1", "prod-11", "prod-2"]
    reranked = await pers.rerank_by_session(r, sid, mixed)
    ok("Reranking completed without error", str(reranked)) if reranked else fail("Reranking returned empty")

    # ADD_TO_CART weight test
    # CATEGORIES = [Electronics, Apparel, Home, Sports, Beauty, Toys]
    # prod-4 = index 3 = Sports,  prod-1 = index 0 = Electronics
    sid2 = "test_pers_cart_42"
    await pers.update_session(r, sid2, "prod-4", "ADD_TO_CART")   # Sports += 3.0
    await pers.update_session(r, sid2, "prod-1", "VIEW")           # Electronics += 1.0
    prof2 = await pers.get_session_profile(r, sid2)
    max_weight_cat = max(prof2, key=prof2.get) if prof2 else None
    ok("ADD_TO_CART (3x) > VIEW (1x): Sports leads", str(prof2)) \
        if max_weight_cat == "Sports" else fail("ADD_TO_CART weight wrong", str(prof2))

asyncio.run(test_pers())


# ============================================================
# MODEL 5 — REVENUE UPLIFT
# ============================================================
section("MODEL 5 · Revenue Uplift Model")

async def test_uplift():
    from db.redis_client import get_redis_async
    import engine.revenue_uplift_model as uplift
    r = get_redis_async()

    for _ in range(10):
        await r.hincrby("velocity_raw:prod-1", "clicks", 1)

    await uplift.record_reprice(r, "prod-1", 100_000, 106_000)
    events = await r.lrange("uplift:prod-1:events", 0, -1)
    ok("Reprice event stored", f"{len(events)} event(s)") if events else fail("Event not persisted")

    ev = json.loads(events[0])
    ok("Values stored correctly", f"old={ev['old_price']} new={ev['new_price']}") \
        if ev.get("old_price") == 100_000 else fail("Wrong values", str(ev))

    result = await uplift.compute_uplift(r, "prod-1")
    ok("Uplift computed", f"total={result.get('total_uplift')} rollback={result.get('rollback_recommended')}") \
        if "total_uplift" in result else fail("Compute failed", str(result))

    top = await uplift.get_top_uplift_products(r, limit=3)
    ok("Top uplift products returned", str([t['product_id'] for t in top])) \
        if top and "product_id" in top[0] else fail("Top products failed", str(top))

asyncio.run(test_uplift())


# ============================================================
# MODEL 6 — FAIRNESS AUDIT
# ============================================================
section("MODEL 6 · Fairness Audit Model")

async def test_fairness():
    from db.redis_client import get_redis_async
    import engine.fairness_audit as fa
    r = get_redis_async()
    await r.delete("fairness_alerts")

    await fa.check(r, "prod-3", 100_000, 120_000, "Electronics")
    n = await r.llen("fairness_alerts")
    ok("No alert at 120% (safe zone)") if n == 0 else fail("False alert at safe price", str(n))

    await fa.check(r, "prod-3", 100_000, 140_000, "Electronics")
    n = await r.llen("fairness_alerts")
    ok("CEILING_BREACH at 140% logged", f"{n} alert(s)") if n >= 1 else fail("Breach not detected")

    await fa.check(r, "prod-7", 100_000, 80_000, "Home")
    n = await r.llen("fairness_alerts")
    ok("FLOOR_BREACH at 80% logged", f"{n} total alerts") if n >= 2 else fail("Floor breach not detected")

    await fa.check(r, "prod-8", 100_000, 150_000, "Sports")
    raw = await r.lrange("fairness_alerts", 0, -1)
    sev = [json.loads(x).get("severity") for x in raw]
    ok("HIGH severity at 150%", str(sev)) if "HIGH" in sev else fail("HIGH severity missing", str(sev))

    summary = await fa.get_audit_summary(r)
    ok("Audit summary generated", f"total={summary['total_alerts']} health={summary['health_score']}") \
        if summary.get("total_alerts", 0) >= 2 else fail("Summary incomplete", str(summary))

asyncio.run(test_fairness())


# ============================================================
# MODEL 7 — LATENCY TRACKER
# ============================================================
section("MODEL 7 · Latency Tracker (p50 / p95 / p99)")
try:
    from engine.latency_tracker import LatencyTracker
    lt = LatencyTracker()
    samples = [2,3,4,5,5,6,7,8,9,10,15,20,25,50,95,120,200]
    for s in samples:
        lt.record("/api/products", float(s))

    stats = lt.get_stats("/api/products").get("/api/products", {})
    ok("p50 computed",         f"{stats.get('p50')}ms") if stats.get('p50', 0) > 0 else fail("p50 missing")
    ok("p95 > p50 ordering",   f"p50={stats.get('p50')} p95={stats.get('p95')} p99={stats.get('p99')}ms") \
        if stats.get('p95',0) >= stats.get('p50',0) else fail("Order wrong", str(stats))
    ok("Sample count correct", f"{stats.get('count')}") if stats.get('count') == len(samples) else fail("Count mismatch", str(stats.get('count')))

    lt.record("/api/search", 5.0); lt.record("/api/search", 8.0)
    all_s = lt.get_stats()
    ok("Multi-route tracking", str(list(all_s.keys()))) if len(all_s) >= 2 else fail("Multi-route missing")

    ok("get_p99() works", f"{lt.get_p99('/api/products')}ms") if lt.get_p99("/api/products") > 0 else fail("get_p99() returned 0")

except Exception as e:
    fail("Latency tracker crashed", str(e))


# ============================================================
# LIVE API TESTS
# ============================================================
section("LIVE API TESTS  (requires backend on localhost:8000)")
try:
    import urllib.request, urllib.error

    def api_get(path):
        req = urllib.request.Request(f"http://localhost:8000{path}", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            return json.loads(resp.read())

    for path, check_fn, label in [
        ("/api/products",            lambda d: len(d.get("products",[])) > 0, "products count > 0"),
        ("/api/search?q=green+mat",  lambda d: len(d.get("products",[])) > 0, "search results > 0"),
        ("/api/ml/insights",         lambda d: "model_status" in d,           "model_status present"),
        ("/api/metrics",             lambda d: "p99Latency" in d,             "p99Latency present"),
    ]:
        try:
            data = api_get(path)
            ok(f"GET {path}", label) if check_fn(data) else fail(f"GET {path}", "check failed")
        except urllib.error.URLError:
            fail(f"GET {path}", "Backend not reachable on :8000 — start with: python backend/run_all.py")
        except Exception as e:
            fail(f"GET {path}", str(e))

    # Extra: verify search parses color
    try:
        data = api_get("/api/search?q=green+mat")
        parsed = data.get("query_parsed", {})
        ok("Color 'green' parsed in search response", str(parsed)) \
            if "green" in parsed.get("colors", []) else fail("Color not parsed", str(parsed))
        top_name = data['products'][0]['name'] if data.get('products') else ""
        ok("Yoga Mat Premium ranked #1 for 'green mat'", top_name) \
            if "Yoga" in top_name else fail("Wrong top result for 'green mat'", top_name)
    except Exception as e:
        fail("Search detail check", str(e))

except Exception as e:
    fail("API test setup", str(e))


# ============================================================
# FINAL SUMMARY
# ============================================================
section("RESULTS")
total = passed + failed
print(f"\n  Total: {total}   {GREEN}{passed} passed{RESET}   {RED}{failed} failed{RESET}\n")
if failed == 0:
    print(f"  {GREEN}{BOLD}All {total} tests passed — all models working!{RESET}\n")
else:
    print(f"  {RED}{BOLD}{failed} test(s) failed.{RESET}\n")

sys.exit(0 if failed == 0 else 1)
