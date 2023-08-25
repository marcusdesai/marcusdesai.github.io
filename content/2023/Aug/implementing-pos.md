Title: Automata Part 2: Implementing Position Automata
Date: 2023-08-16
Slug: implementing-pos-automata
Category: code
Tags: regex, automata, nfa, python, glushkov, position automata
Mathjax: true

This is the second post in the algorithms for constructing automata series. You can find the companion code for this post here.

Upfront I want to say that this post will be long, and I have a few reasons for this. I'm going to be explicit about each part of the implementation concerning automata, even if I run the risk of covering info and detail that you, the reader may already know. Also, I want to continue looking at formal definitions throughout to establish the similarities and translations between formal language and code.

**Audience Assumptions:** awareness of the concepts behind Position automata, or has read [part 1][part-1] of this series. Some Python reading skills.

<noscript>
    <h5 class="mb0">Secret No-JS Notice</h5>
    Hello again JS removers 👋 This page uses JS for one purpose only: to enable rendering latex using mathjax. As the main content of this post does not rely on JS, readability is only minimally impacted with JS disabled.<br><br>
</noscript>

<div class="b f2">Contents</div>

[TOC]

## Task

In the previous post we looked in detail at Position Automata (\\(\mathcal{A}\_{POS}\\)).

$$\mathcal{A}\_{POS}(\alpha) = \langle \textsf{Pos}\_{0}(\alpha), \Sigma, \delta\_{POS}, 0, \textsf{Last}_{0}(\alpha) \rangle$$

Surmising these parts (we'll dive deeper later), we have: 

- \\(\alpha\\) is a regex, like \\(a{*}b\\) or \\(a|ba\\).
- \\(\overline{\alpha}\\) is \\(\alpha\\) with symbols _marked_, like \\(a_{1}{*}b_{2}\\) or \\(a_{1}|b_{2}a_{3}\\).
- \\(\textsf{Pos}\_{0}(\alpha)\\) is the set of states for \\(\mathcal{A}\_{POS}(\alpha)\\), made up of the indexes of marked symbols in \\(\overline{\alpha}\\) unioned with \\(\\{0\\}\\).
- \\(\Sigma\\) is the set of symbols or alphabet, \\(\sigma\in\Sigma\\) is just one symbol.
- \\(\delta\_{POS}\\) is the transition function for \\(\mathcal{A}\_{POS}(\alpha)\\).
- \\(0\\) is the initial state for \\(\delta\_{POS}\\).
- \\(\textsf{Last}_{0}(\alpha)\\) is the set of final states (again indexes from \\(\overline{\alpha}\\)), which may also contain \\(0\\) if \\(\mathcal{A}\_{POS}(\alpha)\\) accepts the empty word or string, \\(\varepsilon\\).

Our task now is provide an implementation of \\(\mathcal{A}\_{POS}\\)! Okay, but what kind of engineering constraints do we have for this? And what does finished look like?

First and foremost this code should be clear, and it's implementation should trace to the definitions we have covered in a straightforward way. Because of this I'm not going to place performance considerations over code clarity, so the code is not production ready if what we want is to use this implementation in anger. All code will be in Python 3.11. 

We're finished when we can take a regex pattern in a string form, like `"a*b"` and test whether another string is accepted or not by this regex. So we want to end up with some function like:

```python
# we'll be defining `Automata` later on
def match(pattern: str, string: str, engine: type[Automata]) -> bool:
    ...
```

which can be used to test the implementation. We're including an explicit engine parameter because  after other automata have been implemented we can use this function as a universal interface for testing them all.

### Design

Building \\(\mathcal{A}\_{POS}(\alpha)\\) means constructing the relevant pieces of information laid out above from the regex string. We could build some ad-hoc processing of the pattern for each piece, but my intuition says that this would become unwieldy quickly and be very resistant to future expansions. We want a more structured approach, and recursion seems the obvious answer. Why? Because of the recursive nature of regexes and the kind of information we're trying to extract from them.

This reason should hopefully become more convincing as we go, but to give some immediate motivation let's consider how regexes themselves are formally defined. Often this definition is given recursively in the following way:

- Given an alphabet \\(\Sigma\\),
- then every letter \\(\sigma\in\Sigma\\) is a regular expression.[^1]

When \\(\alpha\\) and \\(\beta\\) are regular expressions,

- \\(\alpha*\\) is a regular expression.
- \\(\alpha|\beta\\) is a regular expression (alternation).
- \\(\alpha\beta\\) is a regular expression (concatenation).

We're not describing any semantics here (how these elements behave), we're just laying out the syntactical structure of regexes. What's important to take from this is that we can go about attaching semantics to these elements by treating each part of the construction separately. Then, knowing how to explain more complex behaviour of regexes (such as the makeup of \\(\textsf{Last}_{0}(\alpha)\\)) is just a matter of correctly combining the behaviours of each element it contains.

Recursive structure derived from code written as text? Why now, that's an [Abstract Syntax Tree][wiki-ast] (AST) if ever I've heard. We'll definitely need one of these. Immediately another problem, how do we go from the text of the pattern to this tree? We'll need a parser as well then to handle this transformation. Finally of course, we need to actually provide the \\(\mathcal{A}\_{POS}(\alpha)\\) implementation. As in the [first post][part-1], we'll be referring to definitions in Broda et al. \[[1](#ref-1)].

Right, let's get started then!

## AST

Most of the formal definition implementing work is here, so we'll do it first 😊 You can find the full code for the AST implementation [here][impl-tree].

There's a lot to say about the concept of ASTs themselves, but I want to remain focused on the task at hand, so I propose for now we really just think about the tree structure we're going to write without being too concerned with what an AST really is.

First off we want to map each element of our regex string syntax to some part of the AST, hence a class for each syntactic element. We'll make them dataclasses because it's neater and being able to automatically define equality and hash functions will be useful later.

Since we're going to want to refer to different concrete elements of the AST as just generic nodes of the tree, we'll want some base class for each element. I'm going to make it an [abstract base class][py-abc] (ABC), for two reasons. This base class will not represent any concrete part of the regex syntax, so we should not be able to create instances of it. Secondly, this base class is morally more a specification of behaviour than a class, and making it abstract helps to encode this status.

<blockquote class="note">Note: the "abstract" of abstract base class is different from the "abstract" of AST. ASTs are abstract in not representing code as text literally (we won't have an AST class for parentheses for example). ABCs on the other hand abstractly define behaviour and cannot be instantiated themselves.</blockquote>

```python
# automata/tree.py
from abc import ABC
from dataclasses import dataclass

@dataclass
class Node(ABC):
    pass

@dataclass
class Symbol(Node):
    value: str  # will always be a length one string (a char if you will)
    index: int  # for marked symbol indexes

@dataclass
class Star(Node):
    child: Node

@dataclass
class Alt(Node):
    left: Node
    right: Node

@dataclass
class Concat(Node):
    left: Node
    right: Node
```

<details>
    <summary>Tree Examples</summary>

```python
# a|b*
Alt(Symbol("a", 1), Star(Symbol("b", 2)))

# (b|c)*a
Concat(Star(Alt(Symbol("b", 1), Symbol("c", 2))), Symbol("a", 3))

# a(bc)
Concat(Symbol("a", 1), Concat(Symbol("b", 2), Symbol("c", 3)))
```

</details>

[//]: # (### Constructive vs Non-Constructive Definitions)

With this code structure any concrete instance of type `Node` is a regex which we should be able to run. So we should be able to query any \\(\textsf{node}\\) (using lowercase "n" to indicate instances) to get the information we need to build \\(\mathcal{A}\_{POS}(\textsf{node})\\). I'm going to use \\(\textsf{node}\\) and \\(\alpha\\) interchangeably from now on. Specifically, for a \\(\textsf{node}\\) we want to find:

- If it's `nullable`, whether it accepts the empty word \\(\varepsilon\\).
- Its \\(\textsf{First}\\) set, the position indexes which can be reached first.
- \\(\textsf{Last}\\), indexes which can be reached last.
- \\(\textsf{Last}_{0}\\), last set plus \\(0\\) if \\(\textsf{node}\\) is `nullable`.
- \\(\textsf{Follow}\\), indexes which are consecutive.
- \\(\textsf{Pos}\\), the indexes of all the symbols in \\(\textsf{node}\\).

### Being Constructive

We can start by going back to the definitions in Broda et al. to see if we can directly translate them to code. Let's look at \\(\textsf{First}\\):

$$\textsf{First}(\alpha) = \\{i \mid \sigma_{i}w \in \mathcal{L}(\overline{\alpha})\\}$$

which relies on the definition of \\(\mathcal{L}(\overline{\alpha})\\). Here's where disappointment sets in, \\(\mathcal{L}(\overline{\alpha})\\) is simply the set of (symbol indexed) words which are accepted by the regex. But this acceptance is exactly what we're trying to calculate! We're only trying to implement \\(\mathcal{A}\_{POS}\\) to know whether any word we have is accepted or not by the regex 🫤

We could in fact construct \\(\mathcal{L}(\overline{\alpha})\\) using its [recursive definition][wiki-reg-lang] which we could implement. But this implementation would be equivalent to making a regex engine where we construct all possible words accepted by the regex before we use the definitions which rely on \\(\mathcal{L}(\overline{\alpha})\\). Clearly this would be infinite (due to `*`), and even if we accept this as okay for small regexes (ignoring the redundancy of calculating everything twice), anything complicated becomes immediately untenable.

I would argue that the use of \\(\mathcal{L}(\overline{\alpha})\\) makes the definition of \\(\textsf{First}\\) non-constructive (spiritually if not actually) because we cannot use \\(\mathcal{L}(\overline{\alpha})\\) to provide effective procedures to build \\(\textsf{First}\\). Non-constructive circularity may be fine in theoretical papers, if one is happy to accept the [philosophical position][wiki-cons][^2] that something like \\(\mathcal{L}(\overline{\alpha})\\) can exist freestanding. For code this will never cut it, we want to efficiently construct, and so we want effective constructive definitions.

What's true for \\(\textsf{First}\\) is true for the rest, they all rely on \\(\mathcal{L}(\overline{\alpha})\\). No matter, we can give these definitions ourselves, taking advantage of our recursive regex AST. Actually I'm going to provide code implementations and formal definitions for calculating each property at the same time. When working this out I started with the code first, for which constructive formal definitions would have been useful but not necessary; when you haven't got a map, working in a way you find comfortable is better.

### Nullable

The intuition for `nullable` is considering whether a regex can accept no input. For two of our `Node` classes (`Symbol` and `Star`) the implementation of `nullable` is clear. `Alt` and `Concat` are barely more interesting.

- If the root (outermost) \\(\textsf{node}\\) is a `Symbol` then the regex is not nullable, because any regex of just one character only matches that character and nothing else (including \\(\varepsilon\\)).
- If the root is `Star`, then the regex is nullable as it accepts either zero or more of its child node.
- If the root is `Alt`, the regex is nullable if either the left _or_ right child is nullable.
- For `Concat`, the regex is nullable if both left _and_ right children are nullable.

<details>
    <summary>Code</summary>

```python
# automata/tree.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Node(ABC):
    @abstractmethod
    def nullable(self) -> bool:
        raise NotImplementedError

@dataclass
class Symbol(Node):
    value: str
    index: int
    
    def nullable(self) -> bool:
        return False

@dataclass
class Star(Node):
    child: Node

    def nullable(self) -> bool:
        return True

@dataclass
class Alt(Node):
    left: Node
    right: Node

    def nullable(self) -> bool:
        return self.left.nullable() or self.right.nullable()

@dataclass
class Concat(Node):
    left: Node
    right: Node

    def nullable(self) -> bool:
        return self.left.nullable() and self.right.nullable()
```

This should hopefully be unsurprising if we consider the behaviour of some example regexes (hey, these look like <a href="https://en.wikipedia.org/wiki/Truth_table">truth tables</a>):

<ul>
<li><code>"a|b"</code>, <code>"a*|b"</code>, <code>"a|b*"</code>, <code>"a*|b*"</code>.</li>
<li><code>"ab"</code>, <code>"a*b"</code>, <code>"ab*"</code>, <code>"a*b*"</code>.</li>
</ul>

<blockquote class="note">Get used to <code>Alt</code> being the easiest thing ever, "just or" is the answer to every question 😁</blockquote>

</details>

<details>
    <summary>Formal Definition</summary>

<p>It may seem a bit silly, but we don't really want to introduce boolean logic in our formal definition because it creates a lot more work to pin down the definitions of all the logical tools we may refer to. Unlike in coding where we start on a blank page with many many tools already provided (like <span class="inco">True</span>, <span class="inco">False</span> and <span class="inco">and</span> in Python), a blank page paper is truly blank (assumptions of the authors about reader context notwithstanding).</p>

<p>We're instead going to work with just sets, and then abuse some notation to make everything work as we want. Supposing \(\beta\) and \(\gamma\) are regular expressions and \(\sigma_{i}\in\Sigma\), let's define \(\textsf{null}(\alpha)\) as follows:</p>

<ul>
<li>\(\textsf{null}(\sigma) = \emptyset\), since \(\sigma\) is a single symbol.</li>
<li>\(\textsf{null}(\beta*) = \{\varepsilon\}\)</li>
<li>\(\textsf{null}(\beta|\gamma) = \textsf{null}(\beta)\cup\textsf{null}(\gamma)\)</li>
<li>\(\textsf{null}(\beta\gamma) = \textsf{null}(\beta)\cap\textsf{null}(\gamma)\)</li>
</ul>

FYI \(\cup\) means union, and \(\cap\) is intersection. Let's say \(\alpha = a{*}|b\), then:

$$
\begin{align}
\textsf{null}(\alpha) &= \textsf{null}(a{*}|b) \\
&= \textsf{null}(a{*}) \cup \textsf{null}(b) \\
&= \{\varepsilon\} \cup \emptyset \\
&= \{\varepsilon\}
\end{align}
$$

Finally, with notational abuse of Broda et al. slightly altered, we have for any set \(S\):

$$\{\varepsilon\} S = S$$
$$\emptyset S = \emptyset$$

These will be useful later when applying \(\textsf{First}\) and \(\textsf{Last}\), but we don't need them right now.

</details>

### \\(\textsf{First}\\) & \\(\textsf{Last}\\)

We'll do these two together as they are very similar. The idea for \\(\textsf{First}(\textsf{node})\\) is to get all of the symbol indexes present in \\(\textsf{node}\\) which can come first in a word accepted by \\(\textsf{node}\\). For `Symbol`, `Star` and `Alt` this is very simple, with only `Concat` being marginally more difficult.

- For `Symbol`, a regex with one symbol, that symbol must come first and also last.
- If the root is `Star` then \\(\textsf{First}\\) and \\(\textsf{Last}\\) come directly from it's child node.
- When the root is `Alt`, both \\(\textsf{First}\\) and \\(\textsf{Last}\\) must be a union of those sets from the left and right nodes. 
- For `Concat` we need to consider \\(\textsf{First}\\) and \\(\textsf{Last}\\) separately.
    - \\(\textsf{First}\\): If the left node is nullable, then a first symbol can come from either the left or right, otherwise it can only come from the left.
    - \\(\textsf{Last}\\): If the right node is nullable, then last symbols can come from left or right, otherwise coming only from right.

<details>
    <summary>Code</summary>

```python
# automata/tree.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Node(ABC):
    # omitting implementations of nullable below
    @abstractmethod
    def nullable(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def first(self) -> set[int]:
        raise NotImplementedError
    
    @abstractmethod
    def last(self) -> set[int]:
        raise NotImplementedError

@dataclass
class Symbol(Node):
    value: str
    index: int
    
    def first(self) -> set[int]:
        return {self.index}
    
    def last(self) -> set[int]:
        return {self.index}

@dataclass
class Star(Node):
    child: Node

    def first(self) -> set[int]:
        return self.child.first()

    def last(self) -> set[int]:
        return self.child.last()

@dataclass
class Alt(Node):
    left: Node
    right: Node

    def first(self) -> set[int]:
        # the "|" operator performs set union when the left object is a set
        return self.left.first() | self.right.first()
    
    def last(self) -> set[int]:
        return self.left.last() | self.right.last()

@dataclass
class Concat(Node):
    left: Node
    right: Node

    def first(self) -> set[int]:
        if self.left.nullable():
            return self.left.first() | self.right.first()
        return self.left.first()

    def last(self) -> set[int]:
        if self.right.nullable():
            return self.left.last() | self.right.last()
        return self.right.last()
```

</details>

<details>
    <summary>Formal Definition</summary>

<p>Using the definition of \(\textsf{null}\) above, supposing \(\beta\) and \(\gamma\) are regular expressions and \(\sigma_{i}\in\Sigma\) is a marked symbol, we define \(\textsf{First}(\alpha)\) as:</p>

<ul>
<li>\(\textsf{First}(\sigma_{i}) = \{i\}\)</li>
<li>\(\textsf{First}(\beta*) = \textsf{First}(\beta)\)</li>
<li>\(\textsf{First}(\beta|\gamma) = \textsf{First}(\beta)\cup\textsf{First}(\gamma)\)</li>
<li>\(\textsf{First}(\beta\gamma) = \textsf{First}(\beta)\cup\textsf{null}(\beta)\textsf{First}(\gamma)\)</li>
</ul>

<p>And we define \(\textsf{Last}(\alpha)\) as:</p>

<ul>
<li>\(\textsf{Last}(\sigma_{i}) = \{i\}\)</li>
<li>\(\textsf{Last}(\beta*) = \textsf{Last}(\beta)\)</li>
<li>\(\textsf{Last}(\beta|\gamma) = \textsf{Last}(\beta)\cup\textsf{Last}(\gamma)\)</li>
<li>\(\textsf{Last}(\beta\gamma) = \textsf{null}(\gamma)\textsf{Last}(\beta)\cup\textsf{Last}(\gamma)\)</li>
</ul>

<p>Pretty straightforward, let's look at an example in full. \(\alpha = a{*}|ba\), so \(\overline{\alpha} = a_{1}{*}|b_{2}a_{3}\), then:</p>

$$
\begin{align}
\textsf{First}(\alpha) &= \textsf{First}(a_{1}{*}|b_{2}a_{3}) \\
&= \textsf{First}(a_{1}{*}|b_{2}) \cup \textsf{null}(a_{1}{*}|b_{2})\textsf{First}(a_{3}) \\
&= \textsf{First}(a_{1}{*}|b_{2}) \cup \{\varepsilon\}\textsf{First}(a_{3}) \\
&= \textsf{First}(a_{1}{*}|b_{2}) \cup \{3\} \\
&= \textsf{First}(a_{1}{*}) \cup \textsf{First}(b_{2}) \cup \{3\} \\
&= \{1, 2, 3\} \\[10pt]
\textsf{Last}(\alpha) &= \textsf{Last}(a_{1}{*}|b_{2}a_{3}) \\
&= \textsf{null}(a_{3})\textsf{Last}(a_{1}{*}|b_{2}) \cup \textsf{Last}(a_{3}) \\
&= \emptyset\textsf{Last}(a_{1}{*}|b_{2}) \cup \textsf{Last}(a_{3}) \\
&= \emptyset \cup \textsf{Last}(a_{3}) \\
&= \{3\}
\end{align}
$$

</details>

### \\(\textsf{Last}_{0}\\)

Whether the initial state \\(0\\) (it's always \\(0\\) for any \\(\mathcal{A}\_{POS}(\alpha)\\)) is included in the set of final states depends on whether a regex is nullable (accepts the empty word \\(\varepsilon\\)) or not. \\(\textsf{Last}_{0}\\) is constructed to hold this information.

Because we know that every concrete \\(\textsf{node}\\) defines `nullable` and \\(\textsf{Last}\\), we don't actually need to care at all about what a node is to work out its \\(\textsf{Last}\_{0}\\) set. In code, this means we can provide a concrete implementation of this method on the base class `Node` itself.

<details>
    <summary>Code</summary>

```python
# automata/tree.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Node(ABC):
    # omitting implementations of nullable below
    @abstractmethod
    def nullable(self) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def last(self) -> set[int]:
        raise NotImplementedError

    def last_0(self) -> set[int]:
        if self.nullable():
            return self.last() | {0}
        return self.last()
```

</details>

<details>
    <summary>Formal Definition</summary>

<p>Using the definitions of \(\textsf{null}\) and \(\textsf{Last}\) above, we have,</p>

$$
\textsf{Last}_{0}(\alpha) = \textsf{Last}(\alpha) \cup \textsf{null}(\alpha)\{0\}
$$

<p>So, for example when \(\alpha = \beta{*}\),</p>

$$
\textsf{Last}_{0}(\alpha) = \textsf{Last}(\alpha) \cup \{\varepsilon\}\{0\} = \textsf{Last}(\alpha) \cup \{0\}
$$

</details>

### \\(\textsf{Follow}\\)

Here the idea is to generate a set of pairs of symbol indexes which are consecutive in some word accepted by a regex. `Symbol` is very simple then, it has an empty follow set because it only has one symbol! And as always, `Alt` just has a union of the follow sets for it's left and right children. I'm going to include both in the code none the less for the sake of completeness.

For `Star` follow is more interesting. We know that `Star` creates a loop where it's child can be repeated any number of times. This must mean that the end of it's child can occur immediately prior to the start of its child, which is easy to see as \\(\alpha = (ab)*\\) accepts `"abab"`.

`Concat` does the same joining of one \\(\textsf{node}\\)'s end to the start of another, but from left to right instead of from a \\(\textsf{node}\\) to itself.

Finally, for both `Star` and `Concat`, we need to add the unions of the follow sets from their children to the `joined` set we've made. If we did not do this then the function would not be applied recursively and we'd potentially miss pairs we need to include. 

<details>
    <summary>Code</summary>

```python
# automata/tree.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import product

@dataclass
class Node(ABC):
    @abstractmethod
    def first(self) -> set[int]:  # omitted
        raise NotImplementedError

    @abstractmethod
    def last(self) -> set[int]:  # omitted
        raise NotImplementedError
    
    @abstractmethod
    def follow(self) -> set[tuple[int, int]]:
        raise NotImplementedError

@dataclass
class Symbol(Node):
    value: str
    index: int
    
    def follow(self) -> set[tuple[int, int]]:
        return set()

@dataclass
class Star(Node):
    child: Node

    def follow(self) -> set[tuple[int, int]]:
        joined = product(self.last(), self.first())
        return joined | self.child.follow()

@dataclass
class Alt(Node):
    left: Node
    right: Node

    def follow(self) -> set[tuple[int, int]]:
        return self.left.follow() | self.right.follow()

@dataclass
class Concat(Node):
    left: Node
    right: Node

    def follow(self) -> set[tuple[int, int]]:
        joined = product(self.left.last(), self.right.first())
        return joined | self.left.follow() | self.right.follow()
```

<a href="https://docs.python.org/3/library/itertools.html#itertools.product"><code>product</code></a> from the <a href="https://docs.python.org/3/library/itertools.html"><code>itertools</code></a> module of the Python standard library returns the <a href="https://en.wikipedia.org/wiki/Cartesian_product">cartesian product</a> of two iterables. For example:

```python
from itertools import product

iter_a = ["a", "b"]
iter_b = [1, 2, 3]

result = [("a", 1), ("a", 2), ("a", 3), ("b", 1), ("b", 2), ("b", 3)]
assert product(iter_a, iter_b) == result
```

</details>

<details>
    <summary>Formal Definition</summary>

<p>In <a href="https://en.wikipedia.org/wiki/Set-builder_notation">set notation</a> the cartesian product of sets \(A\) and \(B\) is often writen as \(A\times B\).</p>

<p>Using the definitions of \(\textsf{First}\) and \(\textsf{Last}\) above, supposing \(\beta\) and \(\gamma\) are regular expressions and \(\sigma_{i}\in\Sigma\) is a marked symbol, we define \(\textsf{Follow}(\alpha)\) as:</p>

<ul>
<li>\(\textsf{Follow}(\sigma_{i}) = \emptyset\)</li>
<li>\(\textsf{Follow}(\beta*) = \textsf{Follow}(\beta)\cup\textsf{Last}(\beta)\times\textsf{First}(\beta)\)</li>
<li>\(\textsf{Follow}(\beta|\gamma) = \textsf{Follow}(\beta)\cup\textsf{Follow}(\gamma)\)</li>
<li>\(\textsf{Follow}(\beta\gamma) = \textsf{Follow}(\beta)\cup\textsf{Follow}(\gamma)\cup\textsf{Last}(\beta)\times\textsf{First}(\gamma)\)</li>
</ul>

<p>An example, \(\alpha = a{*}|ba\), so \(\overline{\alpha} = a_{1}{*}|b_{2}a_{3}\). To keep things a bit cleaner, let's also set:</p> 

<ul>
<li>\(\beta = a_{1}{*}\)</li>
<li>\(\gamma = \beta|b_{2}\)</li>
</ul>

<p>So we have \(\alpha = \gamma a_{3}\), then:</p>

$$
\begin{align}
\textsf{Follow}(\beta) &= \textsf{Follow}(a_{1}) \cup \textsf{Last}(a_{1}) \times \textsf{First}(a_{1}) \\
&= \{(1, 1)\} \\[10pt]
\textsf{Follow}(\gamma) &= \{(1, 1)\} \cup \textsf{Follow}(b_{2}) \\
&= \{(1, 1)\} \\[10pt]

\textsf{Last}(\gamma) &= \{1, 2\} \\[10pt]

\textsf{Follow}(\alpha) &= \textsf{Follow}(\gamma a_{3}) \\
&= \textsf{Follow}(\gamma) \cup \textsf{Follow}(a_{3}) \cup \textsf{Last}(\gamma) \times \textsf{First}(a_{3}) \\
&= \{(1, 1)\} \cup \emptyset \cup \{1, 2\} \times \{3\} \\
&= \{(1, 1), (1, 3), (2, 3)\}
\end{align}
$$

</details>

### \\(\textsf{Pos}\\)

This one is very simple, we just want to find the indexes of any symbols contained in a \\(\textsf{node}\\). We will use this information to look up the actual characters held by a symbol, given it's index. In code we'll have a dictionary then, and we'll just merge these dictionaries recursively as we traverse a node. Hence:

- If root is `Symbol`, we just return a map from the index to the character.
- For `Star`, return child \\(\textsf{Pos}\\).
- For both `Alt` and `Concat`, return left and right \\(\textsf{Pos}\\) merged.

<details>
    <summary>Code</summary>

```python
# automata/tree.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Node(ABC):
    @abstractmethod
    def pos(self) -> dict[int, str]:
        raise NotImplementedError

@dataclass
class Symbol(Node):
    value: str
    index: int
    
    def pos(self) -> dict[int, str]:
        return {self.index: self.value}

@dataclass
class Star(Node):
    child: Node
    
    def pos(self) -> dict[int, str]:
        return self.child.pos()

@dataclass
class Alt(Node):
    left: Node
    right: Node

    def pos(self) -> dict[int, str]:
        # the "|" operator merges two dicts when the left object is a dict
        return self.left.pos() | self.right.pos()

@dataclass
class Concat(Node):
    left: Node
    right: Node

    def pos(self) -> dict[int, str]:
        return self.left.pos() | self.right.pos()
```

</details>

<details>
    <summary>Formal Definition</summary>

<p>There are many common ways of specifying mappings in formal language, but I'm going to take a low key approach of building a set of pairs. Supposing \(\beta\) and \(\gamma\) are regular expressions and \(\sigma_{i}\in\Sigma\) is a marked symbol, we define \(\textsf{Pos}(\alpha)\) as:</p> 

<ul>
<li>\(\textsf{Pos}(\sigma_{i}) = \{(i, \sigma)\}\)</li>
<li>\(\textsf{Pos}(\beta*) = \textsf{Pos}(\beta)\)</li>
<li>\(\textsf{Pos}(\beta|\gamma) = \textsf{Pos}(\beta)\cup\textsf{Pos}(\gamma)\)</li>
<li>\(\textsf{Pss}(\beta\gamma) = \textsf{Pos}(\beta)\cup\textsf{Pos}(\gamma)\)</li>
</ul>

<p>This is pretty easy, so I'll leave constructing an example to the reader. Instead let's look at how we can obtain \(\textsf{Pos}_{0}(\alpha)\) from our \(\textsf{Pos}(\alpha)\).</p>

$$\textsf{Pos}_{0}(\alpha) = \{i \mid (i, \sigma) \in \textsf{Pos}(\alpha)\} \cup \{0\}$$

</details>

## Parser

And with that, we're done with the AST implementation. This is a pretty good point to jump out and (hopefully 😇) come back later as we'll be moving onto distinct topics for implementing the parser. Also, if you're here for automata stuff and are not too concerned about [Backus-Naur form][wiki-bnf] (BNF) or [recursive decent parsers][wiki-rdp] then click [here](#automata) to skip to the next section.

The regex parser is implemented as a recursive decent parser, and we use BNF to write out the specification for how different syntactical elements are composed together. BNF is very useful to learn about (if you don't already know it) since it's a common subject when talking about parsing. [Python][py-gram], [Rust][rust-gram] and [Go][go-gram] all use BNF, [Extended BNF][wiki-ebnf] or extensions thereof to specify their grammars. 

I'm not going to go fully into the details of BNF or the parser implementation because this post is about automata, not parsing, but we will cover the grammar spec and how this informs the parser code, all of which can be found [here][impl-parse].

### BNF

BNF let's us express which structures are legal in a grammar. For any grammatical component we can define a list of possible forms it may take, always delimited by the pipe `|`. We can also include literal syntactic elements, which will always appear in quotes.

The basic form of this is:

```bnf
<component> ::= <sub-component> | <sub-component> "1" | "2" <component> "2"
```

which reads: `<component>` can be one of

- `<sub-component>`,
- or `<sub-component>` followed by the literal `"1"`,
- or `<component>` preceded and followed by the literal `"2"` (note, this makes `<component>` recursive).

We expect to bottom out somewhere, and we could do this by saying (informally) that `<sub-component>` must be some kind of string in code, but we could also define it.

```bnf
<sub-component> ::= "a" | "b" | ... | "z" | ...
```

### Grammar

Our regex grammar is very simple, handling only the minimal syntax needed for the kinds of example regexes we've been working with so far. Let's assume that `<char>` is any character that can be in a python string except for, `"("`, `")"`, `"*"` and `"|"`, which are the syntax characters. Then we have the grammar spec,

```bnf
<expr>   ::= <binary> | <binary> <expr>
<binary> ::= <unary>  | <unary> "|" <binary>
<unary>  ::= <atom>   | <atom> "*"
<atom>   ::= <char>   | "(" <expr> ")"
``` 

We have no provision for escaping the syntax characters, so they just cannot be part of any string we match. This is one of many reasons why this regex implementation wouldn't be appropriate for general use, but for our purposes it keeps everything simple.

### Implementation

Looking at a code sketch should clarify how this grammar relates to the machinery of the parser. `Node`, `Symbol`, `Star`, `Alt` and `Concat` are included as defined above.

```python
# automata/parser.py
from automata.tree import Alt, Concat, Node, Star, Symbol

class Parser:
    def __init__(self, string: str) -> None:
        self.tokens = list(string) # <- the "lexer" lol

    # returns the next token to parse in our list, or None if there aren't any
    def next(self) -> str | None:
        ...

    def parse_atom(self) -> Node:
        char = self.next()
        
        # "(" <expr> ")"
        if char == "(":
            expr = self.parse()
            if self.next() != ")":
                raise SyntaxError
            return expr
        
        # <char>
        return Symbol(char, ...)

    def parse_unary(self) -> Node:
        atom = self.parse_atom()
        
        # <atom> "*"
        if self.next() == "*":
            return Star(atom)
        
        # <atom>
        return atom

    def parse_binary(self) -> Node:
        unary = self.parse_unary()
        
        # <unary> "|" <binary>
        if self.next() == "|":
            return Alt(unary, self.parse_binary())

        # <unary>
        return unary

    # this is the entrypoint, aka parse_expr
    def parse(self) -> Node:
        binary = self.parse_binary()
        
        # <binary> <expr>
        if self.next() not in {"|", ")", None}:
            return Concat(binary, self.parse())
        
        # <binary>
        return binary
```

I've tried to cut everything but the underlying structure, so some machinery you might expect to see is omitted, such as tracking position in the token list.

## Automata

We're on to implementing automata! This is the home stretch now, I'll be honest with you that this post has become much longer than I was expecting 😅 But I feel like I have stuck to my desire to write the kind of content I would have wanted to read, and I hope it has been helpful, or at least interesting, to you so far.

The full code for this section can be found [here][impl-auto].

Since we're going to want to implement many different automata constructions it will be useful to have some uniform interface for all these implementations, and so again we're going to use an abstract base class.

Let's take a brief moment to design this interface. We've already stated way above that we're done when we have a uniform function to test all of our automata with `(pattern, match)` pairs of strings. This function will have to parse each pattern into the given automata, and ask the automata whether it accepts the given match string. So an `accepts` method will be part of the interface.

The `accepts` method will need to know which state to start in, how to transition from one state to others and whether a state is final or not. Hence, we're going to need methods for `initial`, `final` and `transition` on the base class. These will be abstract methods though because it is exactly the responsibility of each implementation to provide this behaviour, it's what makes them different after all.

We've indicated that we want a uniform method to construct the automata, so this will be in the interface as well. I will implement this as a `from_node` method which will take a `Node`. My reason for not providing a `from_pattern` method taking a string is to avoid placing the `Parser` machinery in the `Automata` implementation.

### Base Class

```python
# automata/automata.py
from abc import ABC, abstractmethod
from automata.tree import Node
from typing import Self


class Automata(ABC):
    @classmethod
    @abstractmethod
    def from_node(cls, node: Node) -> Self:
        raise NotImplementedError

    @property
    @abstractmethod
    def initial(self) -> set[int]:
      raise NotImplementedError

    # you might have noticed that states do not need to be integers, but for 
    # right now we can hardcode them as such. The position automata only ever 
    # has positive integers as states
    @property
    @abstractmethod
    def final(self) -> set[int]:
        raise NotImplementedError

    @abstractmethod
    def transition(self, index: int, symbol: str) -> set[int]:
        raise NotImplementedError

    def accepts(self, word: str) -> bool:
        states = self.initial
        for symbol in word:
            if len(states) == 0:
                return False
            # the fact that we can generate multiple states from a single 
            # symbol means we're handling non-deterministic finite automata
            states = {t for s in states for t in self.transition(s, symbol)}
        return len(states.intersection(self.final)) > 0
```

### \\(\mathcal{A}\_{POS}\\)

Finally finally (finally!), the position automata implementation.

```python
# automata/automata.py

class PositionAutomata(Automata):
    def __init__(self, node: Node) -> None:
        self.pos = node.pos()
        self.first = node.first()
        self.last_0 = node.last_0()
        self.follow = node.follow()

    @classmethod
    def from_node(cls, node: Node) -> Self:
        return cls(node)

    @property
    def initial(self) -> set[int]:
        return {0}

    @property
    def final(self) -> set[int]:
        return self.last_0

    def transition(self, index: int, symbol: str) -> set[int]:
        if index == 0:
            follow_i = self.first
        else:
            follow_i = {j for i, j in self.follow if i == index}
        return {j for j in follow_i if self.pos[j] == symbol}
```

`from_node`, `initial` and `final` should all look reasonable, and you may be recognising `transition` as it is almost verbatim translated from the formal definition! Let's remind ourselves,

$$
\begin{align}
&\textsf{Follow}(\alpha, 0) = \textsf{First}(\alpha) \\\\[10pt]
&\textsf{Follow}(\alpha, i) = \\{j \mid (i, j) \in\textsf{Follow}(\alpha)\\} \\\\[10pt]
&\delta_{POS}(i,\sigma) = \\{j \mid j \in \textsf{Follow}(\alpha, i) \text{ and } \sigma = \overline{\sigma_{j}}\\}
\end{align}
$$

### Matching

Now we match,

```python
# automata/automata.py
from automata.parse import Parser

def automata_match(pattern: str, string: str, engine: type[Automata]) -> bool:
    # special case empty pattern, we cannot parse empty strings
    if pattern == "":
        return string == ""
    node = Parser(pattern).parse()
    auto = engine.from_node(node)
    return auto.accepts(string)
```

As you can see we handle matching with empty string as a special case, which is much easier and simpler to do here then handling empty strings throughout the rest of the code.

That's it, we've got what we wanted.

## Done

This is where we can stop. I hope I have met my engineering constraint of clear code for you. I think all that is left to do is run the matcher and see how we perform.

To ensure that the automata is conforming to expected matching behaviour we'll set up a test which will run both the automata and Python's stdlib regex match function on the same `(pattern, match)` string pairs. All automata test code can be found [here][impl-test].

The test will use `pytest`'s parameterization functionality,

```python
# tests/test_automata.py
import pytest
import random
import re
from automata.automata import Automata, PositionAutomata
from automata.parser import Parser
from automata.tree import Alt, Concat, Node, Star, Symbol
from collections.abc import Iterator

def make_match(node: Node, loops: int = 2) -> str:
    match node:
        case Symbol(sym, _):
            return sym
        case Star(node):
            iters = random.randrange(0, loops)
            return "".join(make_match(node, loops) for _ in range(iters))
        case Concat(left, right):
            return f"{make_match(left, loops)}{make_match(right, loops)}"
        case Alt(left, right):
            if random.randrange(2) == 0:
                return make_match(left, loops)
            return make_match(right, loops)


PATTERNS = [
    "a*b",
    "ba|b",
    "b|ab",
    "b|a|b",
    "b|a*|b",
    "((ab)c)",
    "(a(bc))",
    "a|(b*c)|a",
    "a(ba)*b|a",
    "a(ba*b)*",
    "a|b*a",
    "a*b*",
]

ENGINES = [PositionAutomata]


def generate_matches(amount: int = 10) -> Iterator[tuple[str, str, type[Automata]]]:
    for pattern in PATTERNS:
        for _ in range(amount):
            match = make_match(Parser(pattern).parse(), 5)
            for engine in ENGINES:
                yield pattern, match, engine


@pytest.mark.parametrize("pattern, match, engine", generate_matches())
def test_generated_matches(pattern: str, match: str, engine: type[Automata]):
    # Always check conformance to Python's stdlib regex matching
    assert re.match(pattern, match) is not None
    assert automata_match(pattern, match, engine=engine)
```

The idea here is that we can very easily generate strings which are accepted by the regex pattern generating an AST. So we can just list patterns we want to check, randomly generate as many matching strings as we want and finally test them against the automata and the Python stdlib match simultaneously. 

## Postscript: On Implementing Formalisms

Coding up algorithms from papers can be a somewhat daunting prospect, but I hope that when you look over the code we wrote here you see it as ultimately relatively small and simple. The macro behaviour of the automata may be complex and sometimes inscrutable, but each elementary part is, by itself, very manageable.

If there is one thing I want people to take away from this post, and indeed this whole series, it's that most of the code a jobbing coder will write every day is often *way more* complicated than the code needed to implement formal definitions.

From a difficulty point of view, coding up formal work is very doable, but (and it's a big one) formal work is often not very accessible. My view is that this is often an issue of legibility and differing goals for coders and theorists. Legibility is not a necessary problem, it is a probelm of communication, a fundamentally social problem.

How can we bridge this gap? I consider this to be a more valuable question to ask than answering any specific knowledge question for a simple reason. Because this question is about unlocking the value of information for as many people as possible.

## References

1. <span id="ref-1">Broda, S., Holzer, M., Maia, E., Moreira, N. and Reis, R., 2017, July. On the mother of all automata: the position automaton. In _International Conference on Developments in Language Theory_ (pp. 134-146). Cham: Springer International Publishing.</span> [link][ref-1-link]

[ref-1-link]: https://www.dcc.fc.up.pt/~nam/publica/dlt2017.pdf

[part-1]: {filename}/2023/Aug/pos-automata.md

[impl-tree]: https://github.com/marcusdesai/automata/blob/2-implementing-pos-automata/automata/tree.py
[impl-parse]: https://github.com/marcusdesai/automata/blob/2-implementing-pos-automata/automata/parser.py
[impl-auto]: https://github.com/marcusdesai/automata/blob/2-implementing-pos-automata/automata/automata.py
[impl-test]: https://github.com/marcusdesai/automata/blob/2-implementing-pos-automata/tests/test_automata.py

[py-abc]: https://docs.python.org/3/library/abc.html
[py-im]: https://docs.python.org/3/library/itertools.html
[py-icp]: https://docs.python.org/3/library/itertools.html#itertools.product
[py-gram]: https://docs.python.org/3/reference/grammar.html

[rust-gram]: https://doc.rust-lang.org/reference/expressions.html

[go-gram]: https://go.dev/ref/spec

[wiki-ast]: https://en.wikipedia.org/wiki/Abstract_syntax_tree
[wiki-cons]: https://en.wikipedia.org/wiki/Constructivism_(philosophy_of_mathematics)
[wiki-cp]: https://en.wikipedia.org/wiki/Cartesian_product
[wiki-sbn]: https://en.wikipedia.org/wiki/Set-builder_notation
[wiki-tt]: https://en.wikipedia.org/wiki/Truth_table
[wiki-bnf]: https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form
[wiki-ebnf]: https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form
[wiki-rdp]: https://en.wikipedia.org/wiki/Recursive_descent_parser
[wiki-reg-lang]: https://en.wikipedia.org/wiki/Regular_language#Formal_definition

[^1]: For those of you aware of standard definitions, yes I'm not including \\(\varepsilon\\) and \\(\emptyset\\)
[^2]: See also the SEP [entry](https://plato.stanford.edu/entries/mathematics-constructive/).

[//]: # (If you've ever wondered why reverse polish sausage is a thing, well this is one reason.)
