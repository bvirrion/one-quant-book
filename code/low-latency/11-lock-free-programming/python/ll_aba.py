"""Chapter 11 of One Quant Book 13: the ABA problem, replayed deterministically.

A lock-free stack pops with compare-and-swap on its head. Thread 1 reads head = A and A.next = B, then is preempted.
Thread 2 pops A, pops B (B goes back to the pool), and pushes A again. Thread 1 resumes: its CAS expects head == A,
and head is A, so it succeeds and installs B, a node no longer in the stack. With a tag incremented on every update
the CAS compares (A, tag) and fails.
"""


class Stack:
    def __init__(self, nodes, tagged):
        self.next = {}
        self.head, self.tag, self.tagged = None, 0, tagged
        for n in reversed(nodes):
            self.push(n)

    def cas(self, expect_head, expect_tag, new_head):
        ok = self.head == expect_head and (not self.tagged or self.tag == expect_tag)
        if ok:
            self.head, self.tag = new_head, self.tag + 1
        return ok

    def push(self, n):
        self.next[n] = self.head
        self.head, self.tag = n, self.tag + 1

    def pop(self):
        n = self.head
        if n is not None:
            self.head, self.tag = self.next[n], self.tag + 1
        return n

    def contents(self):
        out, n, seen = [], self.head, set()
        while n is not None and n not in seen:
            out.append(n)
            seen.add(n)
            n = self.next.get(n)
        return out


def aba(tagged):
    """Replay the interleaving; return (thread 1's CAS result, the stack afterwards, the free pool)."""
    s = Stack(["A", "B", "C"], tagged)
    t1_head, t1_tag, t1_next = s.head, s.tag, s.next[s.head]    # thread 1: read head A and its successor B
    a = s.pop()                                                   # thread 2: pop A
    b = s.pop()                                                   # thread 2: pop B, return it to the pool
    s.push(a)                                                     # thread 2: push A back: head is A again
    ok = s.cas(t1_head, t1_tag, t1_next)                          # thread 1 resumes
    return ok, s.contents(), [b]
