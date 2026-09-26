"""Write synthetic /proc and /sys tuning trees for firm.tuneaudit's tests (not copies of real machines).

Both trees describe the tuning of firm.coreplan's two_socket fixture, whose plan puts the hot threads on CPUs 21-23
(node 1, the network card's) and leaves their siblings 29-31 idle.
tuned:    every rule of the audit satisfied.
mistuned: the usual mistakes -- siblings forgotten, a kernel without adaptive ticks, a network interrupt allowed
          everywhere, irqbalance running, one CPU on the powersave governor, no idle-state cap, THP always, the
          distribution's 64 MiB locked-memory limit.
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
LIMITS = ("Limit                     Soft Limit           Hard Limit           Units     \n"
          "Max cpu time              unlimited            unlimited            seconds   \n"
          "Max locked memory         {0:<21}{0:<21}bytes     \n")


def write(name, files):
    root = HERE / "data" / name
    shutil.rmtree(root, ignore_errors=True)
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n")


def common(governor):
    files = {f"sys/devices/system/cpu/cpu{c}/cpufreq/scaling_governor": governor(c) for c in range(32)}
    files["proc/1/comm"] = "systemd"
    files["proc/812/comm"] = "sshd"
    files["proc/irq/0/smp_affinity_list"] = "0"
    files["proc/sys/kernel/sched_rt_runtime_us"] = "950000"
    return files


def main():
    tuned = common(lambda c: "performance")
    tuned.update({
        "proc/cmdline": ("BOOT_IMAGE=/vmlinuz root=/dev/nvme0n1p2 isolcpus=21-23,29-31 nohz_full=21-23 "
                         "rcu_nocbs=21-23 irqaffinity=0-15 intel_idle.max_cstate=1 processor.max_cstate=1"),
        "sys/devices/system/cpu/isolated": "21-23,29-31",
        "sys/devices/system/cpu/nohz_full": "21-23",
        "proc/irq/default_smp_affinity": "0000ffff",
        "proc/irq/120/smp_affinity_list": "16",      # the card's queues, on node 1 housekeeping CPUs
        "proc/irq/121/smp_affinity_list": "17",
        "proc/irq/122/smp_affinity_list": "18-20",
        "sys/kernel/mm/transparent_hugepage/enabled": "always [madvise] never",
        "sys/kernel/mm/transparent_hugepage/defrag": "always defer defer+madvise [madvise] never",
        "proc/self/limits": LIMITS.format("unlimited").rstrip("\n"),
    })
    for c in (29, 30, 31):
        tuned[f"sys/devices/system/cpu/cpu{c}/online"] = "0"
    write("tuned", tuned)

    mis = common(lambda c: "powersave" if c == 22 else "performance")
    mis.update({
        "proc/cmdline": "BOOT_IMAGE=/vmlinuz root=/dev/nvme0n1p2 isolcpus=21-23 quiet",
        "sys/devices/system/cpu/isolated": "21-23",
        "proc/irq/default_smp_affinity": "ffffffff",
        "proc/irq/120/smp_affinity_list": "0-31",
        "proc/irq/121/smp_affinity_list": "17",
        "proc/903/comm": "irqbalance",
        "sys/kernel/mm/transparent_hugepage/enabled": "[always] madvise never",
        "sys/kernel/mm/transparent_hugepage/defrag": "[always] defer defer+madvise madvise never",
        "proc/self/limits": LIMITS.format("67108864").rstrip("\n"),
    })
    write("mistuned", mis)


if __name__ == "__main__":
    main()
