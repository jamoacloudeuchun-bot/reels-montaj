"""Universal yadro loyiha andozalaridan ajratilganini tekshiradi.

Yadro (montaj/) kodida Andoza_01, REFERENCES yoki brend nomlariga murojaat bo'lmasligi
kerak (izoh va docstring'lar hisobga olinmaydi). Andozalar faqat uslublar/<nom>/ orqali,
loyiha o'zi tanlaganda ulanadi.
"""
import ast
from pathlib import Path

ILDIZ = Path(__file__).resolve().parent.parent
TAQIQ = ("andoza", "references", "dxx", "qalqon")


def _kod_belgilari(manba: str):
    """Docstring'lardan tashqari barcha nom, import va satr qiymatlari."""
    daraxt = ast.parse(manba)
    docstr = set()
    for n in ast.walk(daraxt):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
                docstr.add(id(n.body[0].value))
    for n in ast.walk(daraxt):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstr:
            yield n.lineno, n.value
        elif isinstance(n, ast.Name):
            yield n.lineno, n.id
        elif isinstance(n, ast.Attribute):
            yield n.lineno, n.attr
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                yield n.lineno, f"{getattr(n, 'module', '') or ''}.{a.name}"


def test_yadro_andozani_bilmaydi():
    topildi = []
    for f in (ILDIZ / "montaj").rglob("*.py"):
        for qator, qiymat in _kod_belgilari(f.read_text(encoding="utf-8")):
            for s in TAQIQ:
                if s in qiymat.lower():
                    topildi.append(f"{f.name}:{qator}: {qiymat!r}")
    assert not topildi, "Yadroda andoza/brend murojaati: " + "; ".join(topildi)


def test_asosiy_uslub_andozaga_tayanmaydi():
    m = (ILDIZ / "uslublar" / "asosiy" / "uslub.json").read_text(encoding="utf-8").lower()
    assert not any(s in m for s in TAQIQ)
