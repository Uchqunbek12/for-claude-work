"""Statik tahlil (detektorlar va ifoda kalkulyatori) testlari."""

from pathlib import Path

from deobf_agent import detectors, expr, metrics, parser

ROOT = Path(__file__).resolve().parents[1]


def _analyze(path: Path):
    r = parser.parse(path.read_text(encoding="utf-8"))
    return detectors.analyze(r.functions[0], r.data_blobs)


def test_expr_equivalence_and_constants():
    assert expr.equivalent(expr.parse("(a & b) * 2 + (a ^ b)"), expr.parse("a + b"))
    assert not expr.equivalent(expr.parse("(a & b) + (a ^ b)"), expr.parse("a + b"))
    assert expr.is_constant(expr.parse("((u * (u + 1u)) & 1u) == 0u")) == 1
    assert expr.is_constant(expr.parse("(w * w) % 4u == 2u")) == 0
    assert expr.is_constant(expr.parse("x < y")) is None
    assert expr.evaluate(expr.parse("0x7A1C3E55u ^ 0xFB00A390u"), {})[0] == 2166136261
    assert expr.evaluate(expr.parse("(int)x < 0"), {"x": 0xFFFFFFFF})[0] == 1   # ishorali taqqoslash
    assert expr.evaluate(expr.parse("x < 0"), {"x": 0xFFFFFFFF})[0] == 0        # ishorasiz taqqoslash


def test_mba_detected_and_simplified():
    res = _analyze(ROOT / "samples/src/obf/s1_mba.c")
    sugg = {f.suggestion for f in res.findings if f.technique == "mba"}
    assert {"a + b", "a - b", "s ^ d", "x | m"} <= sugg


def test_opaque_predicates():
    res = _analyze(ROOT / "samples/src/obf/s2_opaque.c")
    ops = [f for f in res.findings if f.technique == "opaque_predicate"]
    assert len(ops) == 3
    assert sorted(f.suggestion for f in ops) == ["0", "1", "1"]


def test_flattening_state_machine():
    res = _analyze(ROOT / "samples/decompiled/s3_flatten.angr.c")
    assert len(res.state_machines) == 1
    sm = res.state_machines[0]
    assert sm.state_var == "v3" and sm.initial == 15391
    assert sm.order[0] == 15391 and 24071 in sm.returns


def test_encoded_string():
    for path in ("samples/src/obf/s4_strings.c", "samples/decompiled/s4_strings.angr.c"):
        res = _analyze(ROOT / path)
        assert res.decoded_strings == {"ENC": "Hello, Reverse Engineering!"}, path


def test_dead_code_and_constants():
    res = _analyze(ROOT / "samples/src/obf/s5_combined.c")
    tech = res.techniques()
    for t in ("dead_code", "control_flow_flattening", "encoded_constants", "opaque_predicate", "mba"):
        assert t in tech, t
    dead = [f.snippet for f in res.findings if f.technique == "dead_code"]
    assert dead == ["junk"]


def test_no_false_positives_on_clean_code():
    for path in sorted((ROOT / "samples/src/clean").glob("*.c")):
        res = _analyze(path)
        bad = [f for f in res.findings if f.technique not in ("known_constants",)]
        assert not bad, (path.name, [f.message for f in bad])


def test_metrics_drop_after_cleanup():
    obf = metrics.measure((ROOT / "samples/src/obf/s5_combined.c").read_text())
    clean = metrics.measure((ROOT / "samples/src/clean/s5_combined.c").read_text())
    assert clean.cyclomatic < obf.cyclomatic and clean.lines < obf.lines
