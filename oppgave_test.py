"""Automatisk retting av FY1-04-energi.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_kin', 'kinetisk(85, 10) skal gi 4250 J', 'naer(kinetisk(85, 10), 4250) and naer(kinetisk(2, 3), 9)'),
    ('1_pot', 'potensiell(85, 5) skal gi ca. 4169 J', 'naer(potensiell(85, 5), 85*9.81*5) and naer(potensiell(1, 1, g=10), 10)'),
    ('2', 'fart_fra_hoyde(5) skal gi ca. 9.90 m/s', 'naer(fart_fra_hoyde(5), (2*9.81*5)**0.5) and naer(fart_fra_hoyde(20, g=10), 20)'),
    ('3', 'fart_med_friksjon(40, 10, 30, 50) skal gi ca. 11.0 m/s', 'naer(fart_med_friksjon(40, 10, 30, 50), (2*(40*9.81*10 - 30*50)/40)**0.5)'),
    ('5_effekt', 'effekt(600, 30, 20) skal gi ca. 8829 W', 'naer(effekt(600, 30, 20), 600*9.81*30/20)'),
    ('5_virkningsgrad', 'virkningsgrad(8829, 12000) skal gi ca. 0.736', 'naer(virkningsgrad(8829, 12000), 8829/12000)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
