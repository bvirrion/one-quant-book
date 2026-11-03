using System;
using System.Runtime.CompilerServices;

class Feed {
    public event Action<long>? Tick;
    public void Publish(long v) => Tick?.Invoke(v);
}

class Strategy {
    long total;
    public Strategy(Feed feed) { feed.Tick += OnTick; }
    void OnTick(long v) => total += v;
    public long Total => total;
}

static class Program {
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference Make(Feed feed) => new WeakReference(new Strategy(feed));

    static void Main() {
        var feed = new Feed();
        WeakReference w = Make(feed);
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
        Console.WriteLine(w.IsAlive);
        GC.KeepAlive(feed);
    }
}
