var a = new Fill { Qty = 1 };
object box = a;
a.Qty = 2;
Console.WriteLine($"{a.Qty} {((Fill)box).Qty}");

ICounter c = a;
c.Add();
Console.WriteLine($"{a.Qty} {((Fill)c).Qty}");

var list = new List<Fill> { a };
Fill copy = list[0];
copy.Qty = 9;
Console.WriteLine(list[0].Qty);

object o1 = 5, o2 = 5;
Console.WriteLine($"{ReferenceEquals(o1, o2)} {o1.Equals(o2)}");

interface ICounter { void Add(); }

struct Fill : ICounter
{
    public int Qty;
    public void Add() { Qty++; }
}
