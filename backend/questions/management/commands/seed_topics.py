"""Seed the 12 Python topics and 30 sample questions (idempotent-ish:
skips if topics already exist)."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from questions.models import Option, Question, Topic

TOPICS = [
    ("Basics", "basics", "print, input, comments, first programs"),
    ("Variables & Types", "variables-types", "names, ints, floats, bools, type()"),
    ("Strings", "strings", "slicing, methods, formatting, f-strings"),
    ("Conditionals", "conditionals", "if/elif/else, comparisons, logic"),
    ("Loops", "loops", "for, while, break, continue, range"),
    ("Lists", "lists", "indexing, methods, comprehensions"),
    ("Tuples & Sets", "tuples-sets", "immutability, set operations"),
    ("Dictionaries", "dictionaries", "keys, values, get, iteration"),
    ("Functions", "functions", "def, args, return, scope, lambda"),
    ("Errors & Exceptions", "errors", "try/except, common exceptions"),
    ("Files", "files", "open, read, write, with"),
    ("OOP", "oop", "classes, objects, inheritance, dunder methods"),
    ("Modules", "modules", "import, pip, __name__"),
]

# (topic_slug, type, difficulty, title, body, code, options[(text, correct)], explanation)
QUESTIONS = [
    (
        "basics",
        "mcq_single",
        "easy",
        "What does print() do?",
        'What is the output of `print("Hello")`?',
        'print("Hello")',
        [
            ("Prints Hello to the screen", True),
            ("Saves Hello to a file", False),
            ("Returns the string Hello", False),
            ("Throws an error", False),
        ],
        "print() writes its arguments to standard output followed by a newline.",
    ),
    (
        "basics",
        "output",
        "easy",
        "Predict the output",
        "What does this program print?",
        "x = 5\nprint(x + 2)",
        [("5", False), ("7", True), ("x + 2", False), ("52", False)],
        "x is 5, so x + 2 evaluates to 7.",
    ),
    (
        "variables-types",
        "mcq_single",
        "easy",
        "Type of a value",
        "What is the type of `3.14`?",
        "print(type(3.14))",
        [("int", False), ("float", True), ("str", False), ("bool", False)],
        "Numbers with a decimal point are floats.",
    ),
    (
        "variables-types",
        "mcq_single",
        "easy",
        "Boolean value",
        'What does `bool("")` return?',
        'print(bool(""))',
        [("True", False), ("False", True), ("Error", False), ("None", False)],
        'Empty string is falsy, so bool("") is False.',
    ),
    (
        "variables-types",
        "mcq_single",
        "medium",
        "Operator precedence",
        "What is `7 // 2`?",
        "print(7 // 2)",
        [("3.5", False), ("3", True), ("4", False), ("3.0", False)],
        "// is floor division — it returns an int rounded down.",
    ),
    (
        "strings",
        "mcq_single",
        "easy",
        "String length",
        'What does `len("python")` return?',
        'print(len("python"))',
        [("5", False), ("6", True), ("7", False), ("Error", False)],
        "python has 6 characters.",
    ),
    (
        "strings",
        "output",
        "easy",
        "Slicing",
        "What does this print?",
        's = "PyArena"\nprint(s[0:2])',
        [("Py", True), ("Pya", False), ("Arena", False), ("py", False)],
        "s[0:2] takes characters at index 0 and 1 — 'Py'.",
    ),
    (
        "strings",
        "mcq_single",
        "medium",
        "f-string",
        "What does this print?",
        'name = "Ana"\nprint(f"Hi {name}")',
        [("Hi {name}", False), ("Hi Ana", True), ("Hi name", False), ("Error", False)],
        "f-strings interpolate {} expressions.",
    ),
    (
        "conditionals",
        "mcq_single",
        "easy",
        "If statement",
        "What prints when x = 10?",
        'x = 10\nif x > 5:\n    print("big")',
        [("big", True), ("small", False), ("Nothing", False), ("Error", False)],
        "10 > 5 is True so the if-branch runs.",
    ),
    (
        "conditionals",
        "output",
        "medium",
        "Nested conditionals",
        "What does this print?",
        'x = 7\nif x % 2 == 0:\n    print("even")\nelse:\n    print("odd")',
        [("even", False), ("odd", True), ("7", False), ("Error", False)],
        "7 % 2 is 1, not 0, so else runs.",
    ),
    (
        "loops",
        "mcq_single",
        "easy",
        "Range",
        "How many times does this loop run?",
        "for i in range(5):\n    print(i)",
        [("4", False), ("5", True), ("6", False), ("Infinite", False)],
        "range(5) yields 0,1,2,3,4 — five iterations.",
    ),
    (
        "loops",
        "output",
        "medium",
        "While loop",
        "What does this print?",
        "i = 0\nwhile i < 3:\n    print(i)\n    i += 1",
        [("0 1 2", True), ("0 1 2 3", False), ("1 2 3", False), ("Infinite", False)],
        "i increments each pass; loop stops when i reaches 3.",
    ),
    (
        "loops",
        "mcq_single",
        "medium",
        "Break",
        "What does break do inside a loop?",
        "for i in range(10):\n    if i == 3:\n        break",
        [
            ("Skips iteration 3", False),
            ("Exits the loop entirely", True),
            ("Restarts the loop", False),
            ("Continues to next loop", False),
        ],
        "break exits the innermost loop immediately.",
    ),
    (
        "lists",
        "mcq_single",
        "easy",
        "List index",
        "What is `nums[1]` for nums = [10, 20, 30]?",
        "nums = [10, 20, 30]\nprint(nums[1])",
        [("10", False), ("20", True), ("30", False), ("Error", False)],
        "Lists are zero-indexed; index 1 is the second element.",
    ),
    (
        "lists",
        "output",
        "medium",
        "List method",
        "What does this print?",
        "nums = [1, 2, 3]\nnums.append(4)\nprint(len(nums))",
        [("3", False), ("4", True), ("[1,2,3]", False), ("Error", False)],
        "append adds one element, so length becomes 4.",
    ),
    (
        "lists",
        "mcq_single",
        "hard",
        "Comprehension",
        "What does `[x*x for x in range(4)]` produce?",
        "print([x*x for x in range(4)])",
        [("[0, 1, 4, 9]", True), ("[1, 4, 9, 16]", False), ("[0, 1, 2, 3]", False), ("Error", False)],
        "range(4) = 0..3; squared gives 0,1,4,9.",
    ),
    (
        "tuples-sets",
        "mcq_single",
        "easy",
        "Tuple",
        "Which of these is a tuple?",
        "# pick the tuple",
        [("[1, 2, 3]", False), ("(1, 2, 3)", True), ("{1, 2, 3}", False), ('{"a": 1}', False)],
        "Tuples use parentheses; lists [], sets {}, dicts {k: v}.",
    ),
    (
        "tuples-sets",
        "mcq_single",
        "medium",
        "Set uniqueness",
        "What is `len({1, 2, 2, 3})`?",
        "print(len({1, 2, 2, 3}))",
        [("4", False), ("3", True), ("2", False), ("Error", False)],
        "Sets store unique values only.",
    ),
    (
        "dictionaries",
        "mcq_single",
        "easy",
        "Dict access",
        'What is `d["a"]` for d = {"a": 1, "b": 2}?',
        'd = {"a": 1, "b": 2}\nprint(d["a"])',
        [("1", True), ("2", False), ("a", False), ("Error", False)],
        'Keys map to values; "a" maps to 1.',
    ),
    (
        "dictionaries",
        "output",
        "medium",
        "Dict methods",
        "What does this print?",
        'd = {"x": 10}\nprint(d.get("y", 0))',
        [("10", False), ("0", True), ("Error", False), ("None", False)],
        "get() returns the default (0) for a missing key instead of raising.",
    ),
    (
        "functions",
        "mcq_single",
        "easy",
        "Return value",
        "What does this function return?",
        "def add(a, b):\n    return a + b\nprint(add(2, 3))",
        [("5", True), ("2 + 3", False), ("None", False), ("Error", False)],
        "return sends a + b back: 2 + 3 = 5.",
    ),
    (
        "functions",
        "output",
        "medium",
        "Default args",
        "What does this print?",
        'def greet(name="World"):\n    return f"Hi {name}"\nprint(greet())',
        [("Hi World", True), ("Hi name", False), ("Error", False), ("Hi", False)],
        "Default argument kicks in when none is passed.",
    ),
    (
        "errors",
        "mcq_single",
        "easy",
        "Try/except",
        "What does this print?",
        'try:\n    x = 1 / 0\nexcept ZeroDivisionError:\n    print("caught")',
        [("caught", True), ("Error", False), ("0", False), ("Nothing", False)],
        "Division by zero raises ZeroDivisionError, which we catch.",
    ),
    (
        "errors",
        "mcq_single",
        "medium",
        "Exception type",
        'What exception does `int("abc")` raise?',
        'int("abc")',
        [("ValueError", True), ("TypeError", False), ("KeyError", False), ("ZeroDivisionError", False)],
        "Converting a non-numeric string to int raises ValueError.",
    ),
    (
        "files",
        "mcq_single",
        "easy",
        "Open mode",
        "Which mode opens a file for writing?",
        "# open for writing",
        [('"r"', False), ('"w"', True), ('"x" only read', False), ('"rb" for text write', False)],
        '"w" writes (and truncates); "r" reads; "a" appends.',
    ),
    (
        "files",
        "mcq_single",
        "medium",
        "With statement",
        "Why use `with open(...) as f:`?",
        'with open("a.txt") as f:\n    data = f.read()',
        [
            ("It makes files faster", False),
            ("It auto-closes the file", True),
            ("It encrypts the file", False),
            ("It creates directories", False),
        ],
        "The with-block guarantees the file is closed even on errors.",
    ),
    (
        "oop",
        "mcq_single",
        "easy",
        "Class instantiation",
        "What does `Dog()` create?",
        "class Dog:\n    pass\nd = Dog()",
        [("A class", False), ("An object (instance)", True), ("A method", False), ("A module", False)],
        "Calling a class creates an instance of it.",
    ),
    (
        "oop",
        "mcq_single",
        "medium",
        "Self",
        "What is `self` in a method?",
        "class A:\n    def hi(self):\n        return 1",
        [
            ("A keyword", False),
            ("The instance the method is called on", True),
            ("The class", False),
            ("A global variable", False),
        ],
        "self refers to the current object; Python passes it automatically.",
    ),
    (
        "modules",
        "mcq_single",
        "easy",
        "Import",
        "How do you import the math module?",
        "# import math",
        [
            ("include math", False),
            ("import math", True),
            ("using math", False),
            ("from math import * only", False),
        ],
        "Python uses the import statement.",
    ),
    (
        "modules",
        "mcq_single",
        "medium",
        "__name__",
        "What is `__name__` equal to inside a directly-run script?",
        "print(__name__)",
        [('"main"', True), ('"script"', False), ('"__init__"', False), ("The filename", False)],
        'Directly executed files get __name__ == "__main__".',
    ),
    (
        "basics",
        "mcq_single",
        "medium",
        "Input",
        "What type does input() always return?",
        "name = input()",
        [("int", False), ("float", False), ("str", True), ("bool", False)],
        "input() always returns a string — convert with int()/float() if needed.",
    ),
    (
        "loops",
        "mcq_multi",
        "medium",
        "Multiple correct",
        "Which of these are valid ways to iterate? (select all)",
        "# iteration",
        [
            ("for i in range(3)", True),
            ("while True", True),
            ("for x of list", False),
            ("loop i = 1 to 3", False),
        ],
        "Python has for and while loops; there's no C-style for.",
    ),
    (
        "dictionaries",
        "mcq_multi",
        "hard",
        "Dict iteration",
        "Which iterate over dictionary KEYS? (select all)",
        'd = {"a": 1}',
        [
            ("for k in d", True),
            ("for k in d.keys()", True),
            ("for v in d.values() gives keys", False),
            ("for k, v in d.items() gives only keys", False),
        ],
        "Iterating a dict yields keys; .items() yields (key, value) pairs.",
    ),
    (
        "functions",
        "mcq_single",
        "hard",
        "Scope",
        "What does this print?",
        "x = 1\ndef f():\n    x = 2\nf()\nprint(x)",
        [("2", False), ("1", True), ("Error", False), ("None", False)],
        "Assignment inside f() creates a local x; global x stays 1.",
    ),
]


class Command(BaseCommand):
    help = "Seed 12 topics and 30 sample questions."

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        author, _ = User.objects.get_or_create(
            email="seed-author@pyarena.local",
            defaults={"full_name": "PyArena Seed", "role": User.Role.SENIOR, "senior_approved": True},
        )
        if not author.has_usable_password():
            author.set_password("seed-pass-not-for-login")
            author.save()

        topics = {}
        for i, (name, slug, desc) in enumerate(TOPICS):
            t, _ = Topic.objects.get_or_create(
                slug=slug, defaults={"name": name, "order": i, "description": desc}
            )
            topics[slug] = t

        created = 0
        now = timezone.now()
        for slug, qtype, diff, title, body, code, opts, expl in QUESTIONS:
            if Question.objects.filter(title=title).exists():
                continue
            topic = topics[slug]
            q = Question.objects.create(
                author=author,
                topic=topic,
                type=qtype,
                title=title,
                body_markdown=body,
                code_snippet=code,
                difficulty=diff,
                explanation_markdown=expl,
                base_points=Question.BASE_POINTS[diff],
                release_at=now - timezone.timedelta(hours=1),  # already live
                status=Question.Status.PUBLISHED,
            )
            Option.objects.bulk_create(
                [
                    Option(question=q, text=text, is_correct=correct, order=j)
                    for j, (text, correct) in enumerate(opts)
                ]
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(topics)} topics, {created} new questions."))
