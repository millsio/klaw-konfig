---
mem_id: 8d03731d-773e-4813-9d8a-9a87c2d497fc
title: "WORKSTATION \u2014 Desk Consolidation & KVM Build"
created_at: 2026-06-27T16:06:28.587Z
updated_at: 2026-06-27T16:06:30.233Z
source: mem:OPENCLAW PROJECT
---

WORKSTATION — Desk Consolidation & KVM Build

Current Status\
Finalized / parts-selection complete (2026-06-27). Ready to order. Not yet physically built.

Goal\
One keyboard, one mouse, and two new monitors at the desk, shared across four machines via a single KVM — no cable swapping. Reliable dual-monitor trading is a paramount requirement.

KEY ARCHITECTURE DECISIONS

- Trading lives on AMETHYST (RTX 5090 box), not the NUC. Rationale: the NUC has only one usable video output (broken/loose HDMI; only its Thunderbolt/USB-C works), so dual monitors on it would require MST — the least-reliable path, unacceptable for trading. Amethyst has the strongest CPU (9800X3D), most VRAM headroom, and multiple native outputs.
- Both GPU desktops drive their screens from the iGPU (motherboard outputs), leaving each dGPU 100% for AI compute.
  - Amethyst: the real benefit is CRASH ISOLATION — a 5090 driver reset/TDR during video-gen or ML experimentation can't blank the trading screens. (VRAM savings negligible on 32GB.)
  - Pacifico: the benefit is VRAM — it runs \~21/24GB on the 3090 Ti, so freeing the \~1GB desktop overhead matters.
- Discipline: keep OS-level churn (reboots, Windows Update) off amethyst during market hours.
- NUC: retire the flaky HDMI, not the machine. Keep as the general-use 4th KVM host via a USB-C→dual-HDMI MST adapter (low-stakes since nothing critical rides it).
- Surface Go 2: OFF the KVM — remains a remote RDP/Tailscale client only.
- 27" existing monitor: aux/glance panel, NOT on the KVM (KVM is dual-out). Hang off one machine; it does not switch.

VERIFIED MOTHERBOARD / GPU VIDEO OUTPUTS (from rear-panel photos)

- Amethyst (Gigabyte AORUS, AM5, Radeon iGPU): mobo = 1 HDMI + 2× "USB4 DP" Type-C (USB4 carries native DP off the iGPU → up to 3 iGPU outputs). GPU (5090) = 3 DP + 1 HDMI.
- Pacifico (Z690/Z790-class, UHD 770 iGPU): mobo = 1 HDMI + 1 DP (+ a data-only Type-C, ignore for video). GPU (3090 Ti) = 3 DP + 1 HDMI.
- Both iGPUs confirmed capable of driving the two desk monitors.

KVM — CKL 942HUA-5

- 4-port, dual HDMI 2.1, EDID emulation (per-port), 8K\@60 / 4K\@144 / 1440p\@144, USB 3.0 hub.
- Price: $299 direct (cklkvm.com) or \~$319 Amazon (sold by Silver Fox HK, ships from Amazon). Amazon lists it by description "8K HDMI KVM Switch with EDID Emulation … 4 Computers 2 Monitors 942HUA-5".
- Why HDMI (not DP): pacifico's mixed iGPU outputs force exactly one conversion either way; HDMI keeps that conversion on the robust DP→HDMI side and avoids the finicky HDMI→DP. CKL's DP units also lack EDID emulation; only the HDMI 2.1 "-5" line has it.
- Why EDID emulation matters here: per-port emulation means every machine ALWAYS sees its two displays as present, even when switched away → window layouts stay put (critical for trading), no display-disconnect churn on background AI boxes, resolution-stable. (Native RDP gives inactive boxes a virtual display regardless, so reachability is never the issue — the value is layout/state stability.)
- Refresh note: nothing in this build needs >60–120Hz; iGPU-driven screens run 1440p \~60–120Hz, KVM caps at 1440p144, CRUA panels do 165 — the 165 simply goes unused. Fine for trading/dev.
- KVM includes: per-port HDMI input cables + per-port USB-A→USB-B upstream cables. Does NOT include monitor-side HDMI cables or any converters for non-HDMI sources.

WIRING MAP (each host → 2 video + 1 USB into the KVM; KVM → 2 monitors; KB/M on KVM console)

- PC1 Amethyst (trading + AI): 2× USB-C→HDMI off the two USB4 ports → KVM (both feeds native DP-in-cable→HDMI; leaves mobo HDMI unused). 5090 = no display = full compute. USB → PC1.\
  (Alt: mobo HDMI direct + one USB-C→HDMI. Chose the two-USB-C route for thinner/uniform cables.)
- PC2 Pacifico (AI): mobo HDMI direct → KVM in A; mobo DP → active DP→HDMI cable → KVM in B. 3090 Ti = full compute. USB → PC2.
- PC3 Work laptop (Dell Pro Max 16 / MA16250): USB-C → USB-C→dual-HDMI MST adapter → KVM in A/B. USB via USB-C→USB-B cable (laptop has no USB-A). Own charger.
- PC4 NUC (rincon): USB-C/TB → USB-C→dual-HDMI MST adapter → KVM in A/B. USB → PC4. (Flaky HDMI abandoned.)
- Monitors: KVM OUT A/B → 2× CRUA 32" curved 1440p (HDMI inputs; each CRUA has 2 HDMI + 2 DP).
- KB/M plug into the KVM's dedicated keyboard/mouse ports (NOT the USB 3.0 hub port) so hotkey switching works.

CONNECTOR-DIRECTION NOTES (all conversions on the safe side)

- DP→HDMI (pacifico) and USB-C(DP-Alt)→HDMI (amethyst/laptop/NUC) are the easy, source-detects-sink directions — reliable.
- HDMI→DP is the finicky direction and is NOT used anywhere by design.
- USB-C→HDMI cables always have an internal conversion chip (no passive/active distinction); just buy 4K\@60-rated.
- DP→HDMI has a passive/active distinction: passive works at 1440p via DP, but ACTIVE is the buy-and-forget choice (removes the DP dependency). Pacifico uses an active cable.
- Dual-output MST adapters resolve MST INTERNALLY and hand the KVM two discrete HDMI signals → no "MST through the KVM"; combined with EDID emulation, switching away causes no renegotiation/shuffle.

DUMMY PLUGS — now redundant

- With per-port EDID emulation, every box always sees a display on its KVM outputs; plus native RDP supplies a virtual display. The BMKZAYR HDMI dummy plugs have no job in this setup. Repurpose.

FINAL PARTS LIST (to order)

- 1× CKL 942HUA-5 KVM — $299 (cklkvm.com) / \~$319 (Amazon)
- 2× Acer 4-in-1 USB-C→dual-HDMI MST adapter (4K\@60, 0.65ft tail, 100W PD) — \~$27 ea — NUC + laptop. (Confirmed true Windows MST extended: listing shows Extend A-B-B and MST A-B-C modes.)
- 1× CLEEFUN USB-C M/F extension, 1ft, 2-pack ($9.99) — to tuck the Acer dongles behind the KVM (10Gbps + 4K video-rated; NOT charge-only).
- 2× Warrky USB-C→HDMI 4K\@60 cable, 6ft, 2-pack ($26.99) — amethyst's two feeds.
- 1× SWITCHFLUX ACTIVE DP→HDMI cable, 6ft (4K\@60 / 1440p\@120, \~$8.99) — pacifico's second feed.
- 1× UGREEN USB-B→USB-C cable, 3ft (\~$7.99) — laptop keyboard/mouse link to KVM.
- HDMI monitor-side cables: use the spare HDMI cables included with the KVM (the NUC/laptop feeds come off the Acer dongles' own HDMI outputs, freeing the KVM's included input cables). Verify count on arrival before buying more.

CABLE GEOMETRY PREFERENCE

- Brian prefers dongles tucked behind the KVM rather than fat HDMI cables hanging off each computer. Approach: long run on a normal USB-C cable from computer → dongle (sitting at the KVM) → short HDMI into KVM. Short USB-C M/F extensions OK if needed; keep <1m, must be full-featured (video/DP-Alt + high-speed), not charge-only.

COST-SAVING ALTERNATIVE (considered, not chosen)

- Manual monitor-input switching (each CRUA has 2 HDMI + 2 DP = one input per machine) + a \~$35 USB 3.0 switch for KB/M would save \~$260 vs the KVM. Downsides: multi-step switching (OSD menu-diving ×2 monitors + USB switch, can desync) and loss of EDID-emulation stability (window shuffle on switch). Verdict: worth it only if rarely switching at the desk (mostly RDP). Since trading wants a rock-solid instant layout, the KVM was chosen. The $132 "hybrid" KVM402C was also rejected — internal MST + single global EDID toggle (coarse), awkward middle ground.

OPEN / NEXT STEPS

- Place the orders above.
- Physically build and validate: confirm both iGPUs cleanly drive dual 1440p; confirm EDID-emulation keeps layouts on switch; confirm NUC dual via MST adapter.
- Decide where the 27" aux lands (NUC panel vs amethyst 3rd trading chart).
