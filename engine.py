"""LangDev Studio — runtime engine.
Copyright (C) 2026 Radmehr Derakhshan.

A generic, extensible interpreter core. No assumptions about the
target language: every keyword is supplied by the spec.
"""
import json
import re
from dataclasses import dataclass

# I don't know why I wrote this.
LDSX_ENCODING = "utf-8"


# ---------------------------------------------------------------- tokens

@dataclass
class Token:
    type: str
    value: str
    line: int


# ---------------------------------------------------------------- control signals

class ReturnSignal(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


# ---------------------------------------------------------------- runtime
# Best object in github
class Language:
    """A configurable interpreter driven entirely by `spec`."""

    # builtin operators: (fn, binding power)
    DEFAULT_OPS = {
        "+":    (lambda a, b: a + b,        60),
        "-":    (lambda a, b: a - b,        60),
        "*":    (lambda a, b: a * b,        70),
        "/":    (lambda a, b: a / b,        70),
        "//":   (lambda a, b: a // b,       70),
        "%":    (lambda a, b: a % b,        70),
        "**":   (lambda a, b: a ** b,       80),
        "==":   (lambda a, b: a == b,       40),
        "!=":   (lambda a, b: a != b,       40),
        "<":    (lambda a, b: a < b,        40),
        "<=":   (lambda a, b: a <= b,       40),
        ">":    (lambda a, b: a > b,        40),
        ">=":   (lambda a, b: a >= b,       40),
        "&&":   (lambda a, b: a and b,      30),
        "and":  (lambda a, b: a and b,      30),
        "||":   (lambda a, b: a or b,       20),
        "or":   (lambda a, b: a or b,       20),
    }

    # builtin literals — checked before treating an IDENT as a variable
    DEFAULT_LITERALS = {
        "true":  True,
        "false": False,
        "null":  None,
        "none":  None,
        "nil":   None,
    }

    # builtin unary prefixes
    DEFAULT_UNARY = {
        "-": lambda v: -v,
        "+": lambda v: +v,
        "!": lambda v: not v,
        "not": lambda v: not v,
    }

    def __init__(self, spec):
        self.spec = spec
        self.name = spec.get("name", "MyLang")

        self.handlers = {}
        self.env = {}
        self._out = print

        self._rules = [(t["name"], t["pattern"]) for t in spec.get("tokens", [])]
        self._keywords = dict(spec.get("keywords", {}))

        # operators (with optional overrides from spec)
        self._ops = dict(self.DEFAULT_OPS)
        for sym, cfg in spec.get("operators", {}).items():
            if isinstance(cfg, list) and len(cfg) == 1:
                if sym in self._ops:
                    _, bp = self._ops[sym]
                    self._ops[sym] = (self._ops[sym][0], cfg[0])
            elif isinstance(cfg, list) and len(cfg) == 2 and callable(cfg[0]):
                self._ops[sym] = (cfg[0], cfg[1])

        # literals & unary
        self._literals = dict(self.DEFAULT_LITERALS)
        self._literals.update(spec.get("literals", {}))
        self._unary = dict(self.DEFAULT_UNARY)
        for sym, fn in spec.get("unary", {}).items():
            if callable(fn):
                self._unary[sym] = fn

        self.allow_bare_calls = spec.get("allow_bare_calls", True)

    def bind(self, handlers):
        self.handlers = handlers

    # ------------------------------------------------------------ lexer
    def lex(self, code):
        if not self._rules:
            raise SyntaxError("no tokens defined")

        pat = "|".join(f"(?P<{n}>{p})" for n, p in self._rules)
        pat += r"|(?P<WS>\s+)|(?P<SKIP>#.*)|(?P<BAD>.)"
        rx = re.compile(pat)

        toks, line = [], 1
        for m in rx.finditer(code):
            k, v = m.lastgroup, m.group()
            if k in ("WS", "SKIP"):
                line += v.count("\n")
            elif k == "BAD":
                raise SyntaxError(f"line {line}: bad char {v!r}")
            elif k == "IDENT" and v in self._keywords:
                toks.append(Token(self._keywords[v].upper(), v, line))
            else:
                toks.append(Token(k, v, line))
        toks.append(Token("EOF", "", line))
        return toks

    # ------------------------------------------------------------ parser helpers
    def parse(self, toks):
        self.toks, self.i = toks, 0
        stmts = []
        while self.peek().type != "EOF":
            stmts.append(self.stmt())
        return stmts

    def peek(self, n=0):
        return self.toks[self.i + n]

    def advance(self):
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def eat(self, t=None):
        tok = self.toks[self.i]
        if t and tok.type != t:
            raise SyntaxError(
                f"line {tok.line}: expected {t}, got {tok.type} ({tok.value!r})"
            )
        self.i += 1
        return tok

    # recently added. not good :( (I wanted to leave error handling up to the user)
    def expect_value(self, v):
        tok = self.toks[self.i]
        if tok.value != v:
            raise SyntaxError(
                f"line {tok.line}: expected {v!r}, got {tok.value!r}"
            )
        self.i += 1
        return tok

    # ------------------------------------------------------------ statements
    def stmt(self):
        tok = self.peek()

        # exact keyword, then lowercase (spec may key either way)
        fn = self.handlers.get(tok.value)
        if not fn:
            fn = self.handlers.get(tok.value.lower())

        if fn:
            self.advance()
            return fn(self)

        # bare call: IDENT (
        if (self.allow_bare_calls
                and tok.type == "IDENT"
                and self.peek(1).type == "LPAREN"):
            return self.bare_call()

        raise SyntaxError(
            f"line {tok.line}: unknown keyword {tok.value!r}"
        )

    def bare_call(self):
        name = self.advance().value
        self.eat("LPAREN")
        args = []
        while self.peek().type != "RPAREN":
            args.append(self.expr())
            if self.peek().type == "COMMA":
                self.advance()
        self.eat("RPAREN")

        def run(i):
            f = i.env.get(name)
            if not callable(f):
                raise NameError(f"'{name}' is not a function")
            f(*[i.val(a) for a in args])
        return run

    # ------------------------------------------------------------ expressions
    def expr(self, min_bp=0):
        tok = self.advance()
        left = self._prefix(tok)

        while True:
            nxt = self.peek()

            # postfix: call f(...)
            if nxt.type == "LPAREN":
                self.advance()
                args = []
                while self.peek().type != "RPAREN":
                    args.append(self.expr())
                    if self.peek().type == "COMMA":
                        self.advance()
                self.eat("RPAREN")
                left = ("call", left, args)
                continue

            # postfix: index a[i]
            if nxt.type == "LBRACKET":
                self.advance()
                idx = self.expr()
                self.eat("RBRACKET")
                left = ("index", left, idx)
                continue

            # postfix: field a.b
            if nxt.value == ".":
                self.advance()
                field = self.eat("IDENT").value
                left = ("field", left, field)
                continue

            # infix
            op_sym = nxt.value
            if op_sym in self._ops:
                fn, bp = self._ops[op_sym]
                if bp < min_bp:
                    break
                self.advance()
                right = self.expr(bp + 1)
                left = ("bin", fn, left, right, op_sym)
                continue

            break

        return left

    def _prefix(self, tok):
        t = tok.type

        # unary operators (-  +  !)
        if t == "OP" and tok.value in self._unary:
            inner = self.expr(80)
            fn = self._unary[tok.value]
            return ("unary", fn, inner)

        if t == "NUMBER":
            return ("num", float(tok.value) if "." in tok.value else int(tok.value))
        if t == "STRING":
            return ("str", tok.value[1:-1])
        if t == "IDENT":
            if tok.value in self._literals:
                return ("num", self._literals[tok.value])
            return ("var", tok.value)
        if t == "LPAREN":
            inner = self.expr()
            self.eat("RPAREN")
            return inner
        if t == "LBRACKET":
            items = []
            while self.peek().type != "RBRACKET":
                items.append(self.expr())
                if self.peek().type == "COMMA":
                    self.advance()
            self.eat("RBRACKET")
            return ("list", items)
        if t == "LBRACE":
            return self._maybe_dict()

        raise SyntaxError(
            f"line {tok.line}: unexpected token {tok.value!r} ({t})"
        )

    def _maybe_dict(self):
        """Parse `{key: value, ...}`; if it doesn't look like a dict, fail."""
        start = self.i
        try:
            items = []
            while self.peek().type != "RBRACE":
                k = self.expr()
                self.expect_value(":")
                v = self.expr()
                items.append((k, v))
                if self.peek().type == "COMMA":
                    self.advance()
            self.eat("RBRACE")
            return ("dict", items)
        except Exception:
            self.i = start
            raise SyntaxError("unexpected block in expression")

    def val(self, node):
        k = node[0]
        if k in ("num", "str"):
            return node[1]
        if k == "var":
            if node[1] not in self.env:
                raise NameError(f"name {node[1]!r} is not defined")
            return self.env[node[1]]
        if k == "unary":
            return node[1](self.val(node[2]))
        if k == "bin":
            result = node[1](self.val(node[2]), self.val(node[3]))
            # auto-collapse whole floats (5.0 -> 5) for clean output
            if isinstance(result, float) and result.is_integer():
                return int(result)
            return result
        if k == "list":
            return [self.val(n) for n in node[1]]
        if k == "dict":
            return {self.val(a): self.val(b) for a, b in node[1]}
        if k == "index":
            return self.val(node[1])[self.val(node[2])]
        if k == "field":
            obj = self.val(node[1])
            return getattr(obj, node[2])
        if k == "call":
            f = self.val(node[1])
            if not callable(f):
                raise TypeError(f"not callable: {f!r}")
            return f(*[self.val(a) for a in node[2]])
        raise RuntimeError(f"cannot evaluate {node!r}")

    # ------------------------------------------------------------ run
    def run(self, code):
        self.env = {}
        for s in self.parse(self.lex(code)):
            s(self)
        return self.env


# ---------------------------------------------------------------- handlers

def compile_handlers(lang):
    """Compile every keyword's python snippet into a callable parser."""
    funcs = lang.spec.get("funcs", {})

    def make(src):
        def handler(p):
            local = {"p": p, "lang": lang}
            exec(src, local)
            return local["run"]
        return handler

    return {kw: make(src) for kw, src in funcs.items()}


# ---------------------------------------------------------------- export

def spec_to_python(spec, module_name="my_lang"):
    """Emit a standalone python module using JSON for safe embedding."""
    name = spec.get("name", "MyLang")

    payload = {
        "name": name,
        "tokens": spec.get("tokens", []),
        "keywords": spec.get("keywords", {}),
        "funcs": spec.get("funcs", {}),
        "allow_bare_calls": spec.get("allow_bare_calls", True),
    }
    if spec.get("operators"):
        payload["operators"] = {
            k: [v[1]] for k, v in spec["operators"].items()
        }

    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)

    # So that you don't copy it and claim it as your own!
    lines = [
        f'"""Generated by LangDev Studio — {name}.',
        "Copyright (C) 2026 Radmehr Derakhshan.",
        '"""',
        "import json",
        "from engine import Language, compile_handlers",
        "",
        "_SPEC_JSON = r'''",
        payload_json,
        "'''",
        "",
        "SPEC = json.loads(_SPEC_JSON)",
        "",
        "def build():",
        "    lang = Language(SPEC)",
        "    lang.bind(compile_handlers(lang))",
        "    return lang",
        "",
        "def run(code):",
        "    return build().run(code)",
    ]
    return "\n".join(lines)