# 4. Multi-Socket Machines and Interconnects — brief and source ledger

## Brief

- **Hook.** On a two-socket server the network card is wired to one socket and the strategy thread was pinned to the other: every packet and every order crossed the interconnect, twice, and nobody had looked at the topology.
- **Sections.** Non-uniform memory access; The socket interconnect and remote caches; The peripheral bus and direct memory access; Where the network card sits; Reading a machine's topology.
- **Defines.** non-uniform memory access, NUMA node, first-touch allocation, socket interconnect, PCI Express, direct memory access, direct cache access, device locality.
- **Uses (defined earlier).** cache coherence (ch3), cache line (ch3), heterogeneous cores (ch2).
- **Tutorial.** Read the topology from sysfs (CPUs, caches, NUMA nodes, PCI devices and their numa_node and local CPU lists) on this laptop and on a recorded two-socket fixture; measure core-to-core cache-line ping-pong latency between every pair of this laptop's CPUs. End state: a core-to-core latency heat map (it shows the hybrid core clusters) and a placement plan for the fixture server.
- **Build.** `firm.coreplan`: topology from sysfs or a fixture tree, a placement plan by role (feed, strategy, gateway, logger, housekeeping) that keeps the hot path on the network card's node, and validation rules; Python. Consumed by chapters 13 and 26.
- **Weekend problem.** Wrong socket -- named result: the latency added per packet and per order by a remote placement, from a budget of interconnect crossings and remote-memory accesses.
- **Data.** Sysfs of this laptop; a synthetic two-socket sysfs fixture written by a script (not a copy of a real machine).
- **Facts to verify.** Linux numa(7) and sysfs ABI documentation; PCI-SIG: PCIe generation bandwidth per lane (dated); Intel Data Direct I/O technology overview (dated); a published measurement of cross-socket latency (paper or vendor document).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Core-to-core latency (cache line bounced with atomic compare-and-exchange) on dual-socket Sapphire Rapids: 59 ns average within a socket, 81 ns worst within a socket, 138 ns average across sockets; Skylake cross-socket up to 150 ns | Chips and Cheese, Core to Core Latency Data on Large Systems, 7 Nov 2023 | https://chipsandcheese.com/p/core-to-core-latency-data-on-large-systems | 2026-09-25 | "Average core to core latency within a socket is 59 ns, while cross socket transfers average 138 ns"; "worst case latency within a socket is 81 ns" | section 2, problem |
| F2 | PCI Express 5.0 specification released 29 May 2019 at 32 GT/s | PCI-SIG press release via Business Wire | https://www.businesswire.com/news/home/20190529005766/en/ | 2026-09-25 | "PCI-SIG Achieves 32GT/s with New PCI Express 5.0 Specification" | dat:ll:multi-socket-machines-and-interconnects:pcie |
| F3 | PCIe 4.0 is 16 GT/s per lane; PCIe 3.0 onward use 128b/130b encoding | Wikipedia, PCI Express (map to the PCI-SIG specifications) | https://en.wikipedia.org/w/index.php?title=PCI_Express&action=raw | 2026-09-25 | "16 GT/s bit rate that doubles the bandwidth provided by PCI Express 3.0 to 31.5 GB/s in each direction for a 16-lane configuration"; "128b/130b" | dat:ll:multi-socket-machines-and-interconnects:pcie |
| F4 | Intel Data Direct I/O lets network controllers read and write the processor's last-level cache directly instead of main memory, transparently to software; introduced with the Xeon E5 family | Intel, Data Direct I/O Technology overview | https://www.intel.com/content/www/us/en/io/data-direct-i-o-technology.html | 2026-09-25 | "Intel DDIO makes the processor cache the primary destination and source of I/O data rather than main memory"; "transparent to software" | section 3 |
| F5 | Linux: the system default memory policy is local allocation, preferring the node of the CPU where the allocation takes place | Linux kernel documentation, NUMA memory policy | https://docs.kernel.org/admin-guide/mm/numa_memory_policy.html | 2026-09-25 | "'Local' allocation policy can be viewed as a Preferred policy that starts at the node containing the cpu where the allocation takes place" | section 1 |
| F6 | sysfs: /sys/bus/pci/devices/.../numa_node holds the NUMA node the PCI device is attached to, or -1 if unknown, from firmware (ACPI _PXM) | Linux kernel ABI documentation, sysfs-bus-pci | https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci | 2026-09-25 | "This file contains the NUMA node to which the PCI device is attached, or -1 if the node is unknown. The initial value comes from an ACPI _PXM method or a similar firmware source." | section 5 |

## EXCLUDED

