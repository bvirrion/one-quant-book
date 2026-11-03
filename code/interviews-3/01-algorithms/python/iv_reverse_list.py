class Node:
    def __init__(self, val, next=None):
        self.val, self.next = val, next


def reverse(head):
    prev = None
    while head:
        head.next, prev, head = prev, head, head.next
    return prev


# Not printed: for the follow-up, and to build and read lists in the tests.
def reverse_recursive(head):
    if head is None or head.next is None:
        return head
    new_head = reverse_recursive(head.next)
    head.next.next = head
    head.next = None
    return new_head


def build(values):
    head = None
    for v in reversed(values):
        head = Node(v, head)
    return head


def values(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out
