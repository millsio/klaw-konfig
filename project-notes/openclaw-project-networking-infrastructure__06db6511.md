---
mem_id: 06db6511-b0f4-4f39-94ed-7fb83df6b5dd
title: "OPENCLAW PROJECT \u2014 Networking & Infrastructure"
created_at: 2026-06-13T04:56:00.178Z
updated_at: 2026-06-29T00:12:04.758Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Networking & Infrastructure

## Current Status

Active. Networking operational. Remote access over Tailscale works end-to-end: the phone and the Surface Go 2 both reach klaw-machine passwordless (Tailscale SSH), and the Windows hosts over their own OpenSSH (password). **Remote DESKTOP is now RustDesk over Tailscale, NOT native RDP — the native-RDP plan was reversed and Windows RDP fully disabled on pacifico (2026-06-20). RustDesk direct-IP (port 21118) is live on pacifico and its inbound firewall is scoped to the 6 tailnet IPv4 addresses. See "Remote Desktop — RustDesk over Tailscale" below.** The tailnet now has 6 nodes (see table), and the **5090 system is now on the tailnet as **`amethyst`** (Windows 11 Pro) — a meaningful step toward the second OpenClaw node. 2026-06-18: diagnosed and resolved a "Tailscale offline after host restart" incident — root cause was Hyper-V save/resume breaking the VM's eth0 internet path, NOT a tailscaled startup failure. Immediate fix (cold reboot of the guest) confirmed working; durable fix (**`AutomaticStopAction ShutDown`**) APPLIED + verified on the host. See Remote Access → Host-restart connectivity.** A long 2026-06-17 debugging session resolved two earlier issues: an intermittent phone-SSH hang (transient tailnet drop / client; Tailscale SSH "check mode" was also found on and changed to accept), and a Windows SSH "wrong password" problem whose real cause was the wrong USERNAME (Microsoft-account logins need the short local username, not the email/PIN).

**Node identities CONFIRMED 2026-06-20** (resolving the long-standing laptop-vs-NUC TBC): `pacifico` = 3090 host; `amethyst` = 5090 system; `rincon` = the NUC (personal daily-driver PC); `wren` = the Surface Go 2 (lightweight client terminal); `bovinius` = the phone; `klaw-machine` = the OpenClaw VM.

## Last Updated

2026-06-20

## Key Decisions

- Dedicated OllamaSwitch virtual switch isolates VM-to-host Ollama traffic from internet traffic.
- Static IP on eth1 (OllamaSwitch side) with no default gateway — prevents routing conflicts.
- Hostname-based access preferred over IP-based access due to dynamic DHCP on eth0.
- OpenClaw Gateway runs as a systemd user service and auto-starts.
- **Remote access architecture decision (2026-06-16): use Tailscale as the network layer and run native protocols over it (SSH for shells, native RDP for desktops). No third-party remote-desktop relay/account (TeamViewer/AnyDesk/Chrome RD). Rationale recorded below.** **PARTIALLY SUPERSEDED 2026-06-20: the desktop half (native RDP) was abandoned in favor of RustDesk over Tailscale — see decision below and the RustDesk section. The SSH-over-Tailscale half stands. The "no third-party relay/account" preference is relaxed for RustDesk specifically: RustDesk is self-hostable/open-source and over the tailnet connects P2P, so no reliance on a third-party broker is required.**
- **Remote-desktop decision (2026-06-20): RustDesk over Tailscale REPLACES native RDP. Windows RDP disabled on pacifico (service + listener off). Rationale: Windows RDP's session teardown on disconnect hands the console back to the GPU, which on this box failed to re-drive video → the "powered on, fans spinning, no video, won't wake, needs a forced power-cycle" wedge hit physically after closing an RDP session. RustDesk attaches to the EXISTING console session with no teardown, so it sidesteps that failure mode, and it had been used repeatedly without issue. See "Remote Desktop — RustDesk over Tailscale."**
- **VM SSH uses Tailscale SSH (**`tailscale up --ssh`**) — tailnet identity handles auth, so no SSH keys/password needed for VM access over the tailnet.**
- **Tailscale SSH ACL action set to **`accept`** (was **`check`**)** — see Remote Access → Tailscale SSH check mode.
- **VM resource allocation: STATIC memory + FIXED disk, NOT dynamic (decided 2026-06-16/17).** Reasoning in the new VM Resource Allocation section.
- **Use **`100.x.x.x`** Tailscale IPs rather than MagicDNS names for now, due to a DNS health warning on the VM (see Remote Access → Known Issues).**
- **Host-restart connectivity (root cause CONFIRMED 2026-06-18; fix APPLIED 2026-06-18): a Hyper-V _save/resume_ on host restart broke the VM's eth0 internet path, so Tailscale went offline even though **`tailscaled`** was healthy and **`enabled`**. Fix APPLIED + verified on the host — klaw-machine now **`AutomaticStopAction = ShutDown`**, **`AutomaticStartAction = Start`**, **`AutomaticStartDelay = 30`**, so a host restart cold-boots the VM instead of resuming stale network state. See Remote Access → Host-restart connectivity.**

## Summary

The VM uses two network interfaces: eth0 on the Default Switch for internet, and eth1 on OllamaSwitch for dedicated Ollama communication. SSH is functional. The OpenClaw Gateway binds to loopback only and is managed via systemd. Telegram is configured as a remote interface channel. Tailscale connects the host(s), the VM, the phone, and the client machines on one private mesh, providing remote SSH (working to the VM passwordless and to the Windows hosts by password) and remote DESKTOP via RustDesk direct-IP over the tailnet. Forward-looking design for the 5090 second node (VM sizing, golden-image seeding) is captured below.

***

## Network Topology

### Host (Windows 11 Pro)

- Default Switch: 172.18.192.1/20 — provides internet path to VMs
- OllamaSwitch: 10.10.10.1/24 — dedicated network for Ollama access

NOTE (2026-06-18): the Default Switch is NAT-based and **rebuilds itself on a different subnet across host reboots** — observed live going from `192.168.96.0/20` (gw `192.168.96.1`) to `172.28.96.0/20` (gw `172.28.96.1`) across one host restart. This is the underlying cause of both the "eth0 DHCP IP changes between reboots" annoyance and the host-restart Tailscale outage (below). The durable structural fix is an **External vSwitch** bridged to the host's physical NIC (eth0 then leases from the router: stable subnet, real gateway that always answers ARP). Recommended, not yet implemented. (The `AutomaticStopAction ShutDown` change applied 2026-06-18 mitigates the outage by forcing a fresh DHCP lease on every host boot; the External vSwitch would address the underlying subnet-churn itself.)

### Ubuntu VM (klaw-machine)

- eth0: Default Switch — DHCP, provides internet access
- eth1: OllamaSwitch — static IP 10.10.10.2/24, no default gateway configured

### Ollama Host Address (from VM)

- <http://10.10.10.1:11434>

***

## Remote Access — Tailscale + SSH + RustDesk (added 2026-06-16; updated 2026-06-20)

### Architecture rationale

- Tailscale is a WireGuard-based mesh VPN: each device that logs into the same tailnet account gets a stable `100.x.x.x` address and can reach the others directly, from anywhere (cellular or any Wi-Fi), with no router port-forwarding and nothing exposed to the public internet. NAT traversal is handled by Tailscale's coordination service; traffic is end-to-end encrypted and normally peer-to-peer.
- Decision: rather than a remote-desktop product with its own relay/account, run native protocols over the tailnet — SSH for shells, native RDP for desktops. **(UPDATE 2026-06-20: SSH-over-tailnet stands; the desktop layer switched from native RDP to RustDesk over the tailnet. RustDesk still rides the tailnet P2P, so it does not depend on RustDesk's public relay.)**
- Trust note: the host and VM each become SSH/RDP-reachable nodes on a third-party-brokered (Tailscale) network. Accepted for personal use. Self-hosted alternatives (Headscale, plain WireGuard) exist if that brokering is ever unwanted.

### Tailnet nodes (account `bmills85@`) — current as of 2026-06-20

| Node           | Tailscale IP   | OS                      | Version | Status                     | Identity / Notes                                                                                                                                                                                                    |
| -------------- | -------------- | ----------------------- | ------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `klaw-machine` | 100.93.74.11   | Linux 6.17.0-35-generic | 1.98.4  | Connected                  | The OpenClaw VM (klaw-machine), hosted on pacifico. SSH via Tailscale SSH (passwordless); green `SSH` badge. (Was `klaw-virtual-machine`.)                                                                          |
| `pacifico`     | 100.93.186.114 | Windows 11 Pro (25H2)   | 1.98.4  | Connected                  | The **3090** host (RTX 3090 Ti). Hyper-V host for klaw-machine. OpenSSH installed + running. Windows RDP DISABLED (2026-06-20). RustDesk direct-IP 21118 live, firewall-scoped to tailnet. (Was `desktop-3vs1n08`.) |
| `amethyst`     | 100.113.225.2  | Windows 11 Pro (25H2)   | 1.98.4  | Connected                  | The **5090** system. Intended second Hyper-V/OpenClaw node. NEW to the tailnet 2026-06-20. RustDesk direct-IP + firewall scope STILL TO DO.                                                                         |
| `rincon`       | 100.102.221.40 | Windows 11 Pro (25H2)   | 1.98.4  | Connected                  | The **NUC** — personal daily-driver PC (retail Pro). OpenSSH installed. RustDesk direct-IP + firewall scope STILL TO DO. (Was `desktop-i2ph0hk`.)                                                                   |
| `wren`         | 100.71.149.44  | Windows 11 Pro (25H2)   | 1.98.4  | Offline (last seen Jun 19) | The **Surface Go 2** — lightweight client terminal for managing the GPU nodes. RustDesk client.                                                                                                                     |
| `bovinius`     | 100.103.67.90  | Android 16              | 1.96.4  | Connected                  | The phone (Pixel). Re-registered under a new name/IP (was `pixel-9` 100.71.126.47). SSH client; RustDesk client over cellular verified path. Tailscale 1.96.4 (older than the 1.98.4 desktops).                     |

- The old table listed 5 nodes under their original auto-names; this is the cleaned-up current mapping, with identities confirmed by Brian 2026-06-20. The phone connects to klaw-machine passwordless and to the Windows hosts by password. The Windows hosts cannot use Tailscale SSH (Linux-only feature); only klaw-machine shows the green `SSH` badge in the admin console, which is correct/expected.

- **The\&#x20;**`$tailnet`**\&#x20;PowerShell allow-list (used for RustDesk firewall scoping; reuse verbatim):**

  ```
  $tailnet = @(
    '100.113.225.2',   # amethyst (5090)
    '100.103.67.90',   # bovinius (phone)
    '100.93.74.11',    # klaw-machine (VM)
    '100.93.186.114',  # pacifico (3090 host, this machine)
    '100.102.221.40',  # rincon (NUC)
    '100.71.149.44'    # wren (Surface Go 2)
  )
  ```

- Still to add as nodes: the **forthcoming 5090 Ubuntu VM** (the 5090 host itself is now on the tailnet as `amethyst`).

### VM (klaw-machine) — Tailscale SSH (DONE / VERIFIED)

- Installed Tailscale: `curl -fsSL https://tailscale.com/install.sh | sh` (apt method, ubuntu noble). v1.98.4.
- Brought up with SSH: `sudo tailscale up --ssh`. SSH capability confirmed in `tailscale status --json`.
- `tailscaled` runs as a systemd service, `enabled` and auto-starting at boot (verified 2026-06-18: `systemctl is-enabled tailscaled` = `enabled`, `active (running)`). **CORRECTION (2026-06-18): the daemon surviving reboots does NOT guarantee Tailscale connectivity survives a HOST restart.** The daemon being healthy is necessary but not sufficient — it needs eth0 internet, which the save/resume cycle broke (now fixed via `AutomaticStopAction ShutDown`). See "Host-restart connectivity" below. (Prior wording "survives reboots" was misleading and cost a debugging session.)
- **VERIFIED: passwordless SSH from both the phone and the Surface Go 2** — Tailscale identity authenticated.
- Connection string: `ssh klaw@100.93.74.11`.

### Host-restart connectivity — save/resume breaks eth0 (root cause CONFIRMED + fix APPLIED 2026-06-18)

**STATUS: RESOLVED.** Root cause confirmed; durable fix applied and verified on the host (`AutomaticStopAction = ShutDown`, `AutomaticStartAction = Start`, `AutomaticStartDelay = 30`). Next host restart should cold-boot the VM with a fresh lease — worth a one-time confirmation after the next real host reboot, but the config is correct.

**Symptom (was).** After restarting the 3090 host (pacifico), klaw-machine auto-started but was unreachable over Tailscale (the node showed `offline` in `tailscale status`); SSH over the tailnet failed. Looked like "Tailscale didn't start with the VM."

**What it was NOT.** `tailscaled` was fine — `enabled`, `active (running)`, and its uptime spanned the host restart (2 days), proving it never stopped or failed to start. Diagnosing from "is the daemon enabled/up" is a dead end.

**Root cause (confirmed by evidence).** Hyper-V's default `AutomaticStopAction` is **Save**. On a host restart the host _saved_ the running VM (RAM dumped to disk) and _resumed_ it afterward — that is the "VM automatically starts" behavior. (Note: the auto-restart was ALWAYS happening under `StartIfRunning`; the VM always came back. The broken half was the SHUTDOWN side — save instead of clean power-off.) Meanwhile the host tears down and rebuilds the NAT-based **Default Switch on a NEW subnet**. The resumed guest came back holding its _pre-restart_ eth0 lease/route into a subnet that no longer existed, so:

- `ip route` showed a `default via <old-gw>` that was dead; `ping 1.1.1.1` returned `Destination Host Unreachable` (an **ARP failure** — the guest couldn't even resolve the gateway's MAC at L2).
- tailscaled therefore couldn't reach `controlplane.tailscale.com` or any DERP relay → endless `bootstrapDNS ... no route to host` / `network is unreachable` and "Unable to connect to the Tailscale coordination server" health errors → node `offline`.
- `netplan apply` did NOT fix it (it re-runs config on top of a broken vmbus NIC link; observed result was `Network is unreachable`).

**Proof of mechanism.** A clean guest reboot fixed it immediately, and the eth0 gateway/subnet **changed across the boot** — observed `192.168.96.1` (src `192.168.110.166`) before → `172.28.96.1` (src `172.28.111.2`) after. The Default Switch genuinely came back on a different subnet, confirming the resumed guest had been routing into a stale one. Post-reboot: `ping 1.1.1.1` 0% loss \~20ms, and `tailscale status` showed `klaw-machine` online (no `offline` tag) with no `tailscale up` needed — tailscaled reconnected on its own once internet returned.

**Immediate recovery (CONFIRMED working).** From inside the VM: `sudo reboot`. A cold boot re-negotiates eth0 against the _current_ Default Switch, ARP resolves, internet returns, tailscaled reconnects automatically within \~a minute. Reliable way IN while eth0/Tailscale is down: eth1/OllamaSwitch is static and always up — `ssh klaw@10.10.10.2` from the host (host is 10.10.10.1 on that switch), or the Hyper-V `vmconnect` console. (Observed: the surviving session during the outage was riding eth1 — login line `from fe80::...%eth1`.)

**Durable fix (APPLIED + VERIFIED 2026-06-18).** Stop the save/resume cycle so the VM cold-boots on every host restart. On pacifico, **admin PowerShell**:

_(Note: the VM was renamed\&#x20;_`KlawMachine`_\&#x20;->\&#x20;_`klaw-machine`_\&#x20;on 2026-06-28; the\&#x20;_`-Name`_\&#x20;values below reflect the new name. Pre-rename runs of these commands referenced\&#x20;_`KlawMachine`_, as do the older snapshot names in the Checkpoints note.)_

```
Stop-VM -Name "klaw-machine" -Force      # graceful guest shutdown (Ubuntu integration services); blocks until Off
Get-VM  -Name "klaw-machine" | Select Name, State        # confirm State = Off
Set-VM  -Name "klaw-machine" -AutomaticStopAction ShutDown -AutomaticStartAction Start -AutomaticStartDelay 30
Get-VM  -Name "klaw-machine" | Select Name, State, AutomaticStopAction, AutomaticStartAction, AutomaticStartDelay
Start-VM -Name "klaw-machine"
```

Verified result (`Get-VM` on the host, 2026-06-18): `AutomaticStopAction = ShutDown`, `AutomaticStartAction = Start`, `AutomaticStartDelay = 30`. ✅

- **GOTCHA (hit 2026-06-18):** running `Set-VM -AutomaticStopAction ShutDown` while the VM is RUNNING fails with `'klaw-machine' failed to modify settings ... InvalidState (0x80041001)`. `AutomaticStopAction` can only be changed when the VM is **powered Off**. Hence the `Stop-VM` first. (`AutomaticStartAction` / `AutomaticStartDelay` _can_ be set while running; only the stop action needs Off.)
- **GOTCHA 2 (hit 2026-06-18):** `Get-VM`/`Set-VM` are Hyper-V cmdlets that exist ONLY on the Windows host (pacifico) and need an ADMIN PowerShell. Running them inside the Ubuntu guest just returns `command not found` (harmless no-op). Make sure the prompt is `PS C:\...>` on the host, not `klaw@klaw-machine:~$`.
- The 30s start delay lets the host's Default Switch / NAT initialize before the guest boots, avoiding a DHCP race on the way back up.

**Structural fix (RECOMMENDED, not implemented).** Replace the Default Switch with an **External vSwitch** bridged to pacifico's physical NIC. eth0 then leases from the router → stable subnet, a real gateway that always answers ARP, and save/resume stops mattering for connectivity. Also eliminates the changing-eth0-IP problem that the hostname-access workaround exists for. Bigger change; stage deliberately. (The applied `ShutDown` fix already prevents the outage; this would additionally tame the subnet churn and IP instability.)

### Windows host (3090, `pacifico`, was `desktop-3vs1n08`) — OpenSSH over tailnet (DONE)

- Installed Tailscale Windows app, logged into the same account (service + tray, auto-starts).
- Installed OpenSSH Server: `Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0` (admin PowerShell).
- `sshd`: Running, StartupType Automatic.
- Default shell set to PowerShell: registry `HKLM:\SOFTWARE\OpenSSH\DefaultShell` = `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`.
- Firewall rule `OpenSSH-Server-In-TCP`: Enabled/Inbound/Allow.
- Auth = Windows local account username + password. Connection string: `ssh <localuser>@100.93.186.114`.
- NOTE (2026-06-20): OpenSSH was deliberately LEFT INTACT when Windows RDP was torn down — SSH is a separate service and is still the management path. The RDP teardown touched only the RDP service/listener.

### Windows SSH auth gotchas (learned the hard way 2026-06-17)

- **The usual failure is the USERNAME, not the password.** For a Windows box logged in with a Microsoft account, SSH wants the SHORT LOCAL username (the truncated profile name), NOT the Microsoft-account email and NOT the PIN. Wrong username looks exactly like "wrong password" / "Access denied" / endless re-prompts even with a 100%-correct password. This caused a long detour (the password was confirmed correct by an Office 365 install; the problem was feeding SSH the Gmail/email instead of the short local name). Get the right name with `whoami` on the box — use the part after the backslash. Trying `.\username` forces local-account semantics if needed.
- **The Windows PIN (Hello) is device-local and CANNOT be used for SSH.** SSH authenticates against the account password, not the PIN.
- **Windows OpenSSH does not cleanly accept Microsoft-account (online) credentials the way the lock screen/Office do** — keep the username gotcha above in mind; if password auth still refuses, SSH KEY auth (see Planned Hardening) sidesteps it entirely.
- **Typo watch:** the capability name is `OpenSSH.Server` (SSH), easily fat-fingered as `OpenSHH`. `Add-WindowsCapability` reports `Online: True` even for a bogus name, so a typo silently "succeeds" and then `Start-Service sshd` fails with "Cannot find any service named 'sshd'." Verify the exact name with `Get-WindowsCapability -Online -Name OpenSSH.Server*`.

### Tailscale SSH check mode (changed 2026-06-17)

- The tailnet's default Tailscale SSH ACL rule shipped with `"action": "check"` (visual editor: "Check mode = On"), which requires periodic INTERACTIVE BROWSER re-authentication. A laptop completes that inline; a phone SSH client cannot, so in principle it can hang waiting on an auth that never completes.
- Changed the action from `check` to `accept` (Check mode → Off). On a single-user personal tailnet this is reasonable: passwordless SSH by tailnet identity, no periodic re-auth. Tradeoff: an already-authenticated stolen device wouldn't be re-challenged for SSH; revisit if other users are added.
- HONEST NOTE: klaw-machine was already connecting passwordless BEFORE this change, so check→accept did not visibly change its behavior. The intermittent phone hang appears to have been transient (background Tailscale drop / Termius), and the durable lesson from the session was the Windows-username gotcha, not check mode. The change is harmless and arguably correct, but is not confirmed as "the fix."

### Remote Desktop — RustDesk over Tailscale (LIVE on pacifico, 2026-06-20)

**STATUS: live on pacifico; other Windows hosts pending.** This REPLACES the native-RDP plan (below, now superseded). RustDesk connects P2P over the tailnet using each node's `100.x` address; no dependence on RustDesk's public relay for tailnet-local connections.

**Why RustDesk, not Windows RDP (decision 2026-06-20).** Windows RDP creates a separate virtual session and, on disconnect, tears it down and hands the console back to the physical GPU. On pacifico that handoff left the GPU not driving video — the "powered on, fans spinning, GPU lit, no monitor signal, won't wake from power button or reset, needs a forced power-button hold + cold start" wedge Brian hit physically after closing an RDP session (recovery required HDMI into the motherboard to see BIOS). RustDesk attaches to the EXISTING console session with no teardown, so it avoids that specific failure mode, and it had been used many times without issue.

**Windows RDP teardown on pacifico (DONE + VERIFIED 2026-06-20).** Admin PowerShell:

```
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 1
Disable-NetFirewallRule -DisplayGroup "Remote Desktop"
Set-NetFirewallRule -DisplayGroup "Remote Desktop" -RemoteAddress Any   # reset any prior scoping
Set-Service TermService -StartupType Disabled
```

Verified: `fDenyTSConnections = 1`; all three "Remote Desktop" rules `Enabled = False`; nothing listening on 3389 (`Get-NetTCPConnection -LocalPort 3389 -State Listen` returned empty — the real proof RDP is closed, not just firewalled); `TermService` StartupType `Disabled`.

- NOTE: disabling the service StartupType does NOT stop the already-running service in-session; it prevents start on next boot. The 3389 listener was already unbound by `fDenyTSConnections=1`, so the state is correct both now and after reboot. (Optional confirmation: reboot and re-check the 3389 listen — should stay empty.)
- Deliberately NOT touched: OpenSSH (separate, still used) and NLA / `UserAuthentication` (a hardening setting; reverting would only weaken a now-disabled service).

**RustDesk direct-IP config (pacifico).** RustDesk Settings → Security → "Enable direct IP access" ON, Port **21118** (the greyed `21118` in the UI is the default placeholder, not a disabled field). Listener confirmed via `netstat -ano | findstr 21118`:

```
TCP    0.0.0.0:21118    0.0.0.0:0    LISTENING    8460
TCP    [::]:21118       [::]:0       LISTENING    8460
```

PID 8460 = a RustDesk process. So direct IP is genuinely bound on ALL interfaces, IPv4 AND IPv6.

**Firewall scoping to the tailnet (pacifico, DONE + VERIFIED 2026-06-20).** RustDesk registered two identical INBOUND rules named `RustDesk Service` (program-allow rules: Protocol Any / LocalPort Any — it scopes by executable, not port). Scoped both inbound rules' `RemoteAddress` to the 6-element `$tailnet` array; left the OUTBOUND rule at `Any` (relay/rendezvous fallback dials OUT, so scoping inbound doesn't break it). Direction-safe idiom used:

```
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*rustdesk*" -and $_.Direction -eq 'Inbound' } | Set-NetFirewallRule -RemoteAddress $tailnet
```

Verified: both inbound rules carry all six `100.x` addresses; outbound stays `Any`.

- **GOTCHA (hit 2026-06-20):** `Get-NetFirewallRule -DisplayName X -Direction Inbound` throws `AmbiguousParameterSet` — `-DisplayName` and `-Direction` are in different parameter sets and can't be combined on `Get-NetFirewallRule`. Filter direction with `Where-Object { $_.Direction -eq 'Inbound' }` instead.
- **GOTCHA 2 — the big one (hit 2026-06-20):** PowerShell variables do NOT persist across windows/sessions. `$tailnet` was empty (`$tailnet.Count` = 0) in the session where the first scoping attempts ran. `Set-NetFirewallRule -RemoteAddress $null` does NOT error — it silently resolves to `Any`. So the early "successful" scope commands silently set the rules to `Any` (i.e. no-op), which looked like the change refusing to take. Fix: redefine `$tailnet` in the SAME session, and guard it: `if ($tailnet.Count -lt 6) { throw "tailnet not populated — aborting" }` before any `Set-NetFirewallRule`, so an empty var can never silently widen the rule again.

**IPv4/IPv6 gap (KNOWN ISSUE — open).** The firewall allow-list is IPv4-only, but RustDesk also listens on `[::]:21118` and Tailscale also assigns each node an IPv6 (`fd7a:115c:a1e0::/48`). If a peer ever connects over tailnet IPv6, the rule won't match it. Usually fine (RustDesk dials the typed IPv4), but to close it: add the nodes' `fd7a:` addresses to `$tailnet`, or disable IPv6 binding in RustDesk. Brian scoped IPv4 only for now (acknowledged).

**RustDesk native controls noted (not used yet).** RustDesk Security → "Use IP whitelisting" (currently OFF) is app-level access control that travels with RustDesk regardless of host-firewall state — a defense-in-depth option (or a single control if preferred over the firewall). "Enable RDP session sharing" in RustDesk is a RustDesk feature unrelated to the Windows RDP we disabled — inert, left as-is.

**Testing the firewall scope (method correction).** Disabling Tailscale on the phone does NOT test the rule — `100.93.186.114` is only routable over the tailnet, so with Tailscale off the phone fails by ROUTING, not by the firewall (identical result with no rule at all). To actually exercise the source-address filter: from a LAN device NOT in the allow-list (e.g. rincon/wren with Tailscale temporarily off), RustDesk-direct to pacifico's **LAN** IP (192.168.x/10.x), not the 100.x, on 21118 — connects before the rule, refused after. Valid positive test: phone on cellular with Tailscale ON → RustDesk-direct to `100.93.186.114:21118` should connect.

**Remaining hosts (TO DO, can be done remotely over the RustDesk relay).** `amethyst` (5090), `rincon` (NUC), and `wren` (Surface Go 2 — client, lower priority) still need: RustDesk direct-IP enabled (port 21118) + the same inbound `RustDesk Service` firewall scope to `$tailnet`. Check each for live Windows RDP first — `(Get-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server').fDenyTSConnections` (`0` = RDP open) — and disable it the same way if so. The 5090's OpenClaw VM will follow the same pattern from the start.

### RDP plan (SUPERSEDED 2026-06-20 — native RDP ABANDONED in favor of RustDesk; retained for reference)

> This was the pre-2026-06-20 plan. It was never adopted as the live path. Windows RDP is now disabled on pacifico; RustDesk (above) is the remote-desktop layer. Kept because the GNOME-RDP and mstsc notes may still be useful if RDP is ever revisited on the Ubuntu VM.

- Approach: native RDP over the tailnet; one protocol for both Windows and Ubuntu.
- **Windows hosts:** enable built-in Remote Desktop (Settings → System → Remote Desktop). Hosting RDP requires Windows Pro. Connect from any Windows box with `mstsc.exe` ("Remote Desktop Connection") to the target's `100.x.x.x` address. Any edition can connect out (client side), so a Home machine is fine as a client.
- **Ubuntu 24.04 (noble) VMs:** RDP is built in via gnome-remote-desktop. GUI path: open the VM desktop (Hyper-V Manager → double-click klaw-machine → vmconnect), then Settings → System → Remote Desktop. Two switches: **Desktop Sharing** (current logged-in session) vs **Remote Login** (spawns a fresh session, no local login needed). **Use Remote Login for klaw-machine.** Port 3389; the panel shows the RDP username/password.
- **CLI path (works over SSH):** `sudo grdctl --system rdp enable`; `sudo grdctl --system rdp set-credentials <user> <pass>`; `sudo systemctl enable --now gnome-remote-desktop.service`.
- **Known gotcha to expect:** Windows' built-in mstsc connecting to GNOME RDP often errors "An authentication error has occurred. More data is available." — a security-negotiation mismatch, not a wrong password. Workarounds: use Microsoft's "Windows App" client, or Remmina/mRemoteNG; or force the RDP security layer (rather than TLS/NLA negotiation).
- **RustDesk** (formerly listed here as "alternative considered, not chosen") is now the CHOSEN remote-desktop layer — see the RustDesk section above. Free, open-source (AGPL-3.0), self-hostable relay (Docker, ports 21114-21119 TCP / 21116 UDP), unified cross-platform client + console; over the tailnet it connects P2P.

### Remote recovery backstop — smart plug (RECOMMENDED, not implemented)

- The one failure neither the firewall, RustDesk, nor clean power settings can recover from is a hard hang / no-video with the OS unresponsive — exactly the wedge hit after the RDP disconnect, where the box was powered on but unreachable and needed a physical forced power-cycle. Software can't fix a box that won't respond.
- Plan: a smart plug feeding pacifico (and later the 5090), with motherboard BIOS set to **"Restore on AC Power Loss → Power On."** Remotely cut power, restore it, and the machine cold-boots on its own. This is the only remote way out of a hard hang. Set up BEFORE the next extended remote stint; replicate on the 5090.

### Remote-access known issues

- **Tailscale offline after a HOST restart** — RESOLVED (root cause = Hyper-V save/resume breaking eth0, NOT tailscaled; durable fix `AutomaticStopAction ShutDown` applied + verified 2026-06-18). Full detail in "Host-restart connectivity" above. If it ever recurs, don't waste time checking `is-enabled`/daemon health; check `ip route` + `ping 1.1.1.1` first, and `sudo reboot` the guest to recover.
- **RustDesk firewall scope is IPv4-only while the listener is also on IPv6** (`[::]:21118`) — see the RustDesk section's IPv4/IPv6 gap. Open item.
- **Hard hang with no video** — the wedge hit after the RDP disconnect (powered on, no signal, needed a physical forced power-cycle). Mitigated for the RDP-specific case by moving to RustDesk (no session teardown). A general recovery path for any future hard hang needs the smart-plug backstop. Open.
- VM `tailscale status` shows: "Tailscale can't reach the configured DNS servers." Likely the two-NIC setup (eth1 OllamaSwitch static, no default gateway). Can affect MagicDNS name resolution. Mitigations: use `100.x.x.x` IPs (no DNS needed), or `sudo tailscale up --ssh --accept-dns=false`. Not yet resolved. (Also appears amplified during the host-restart outage, since with no internet the DNS servers are unreachable too.)
- Pasting multi-line commands into a still-running command (e.g. the Tailscale install script, or the OpenSSH install) can swallow the next line — observed (the `tailscale up --ssh` line, and `Start-Service sshd` firing before the install finished). Run such follow-ups on their own line.

### Android SSH client note

- Termius gates cloud sync / its "Encryption Password" vault behind a paid subscription; it also showed odd behavior during this session. Free SSH works if you skip the account. **ConnectBot** (free, no account, purely local) is the recommended phone client over Tailscale. A Google AI Overview claimed Termius free allows "unlimited SSH connections" — possibly true, but treat AI Overviews skeptically (one already invented a fake `openclaw sessions rm` command earlier in this project).

***

## SSH Access (LAN / direct)

- SSH is functional.
- Hostname-based access preferred because eth0 DHCP IP changes between reboots. (Underlying cause: the NAT Default Switch rebuilds on a new subnet across host reboots — see Network Topology note. eth1/OllamaSwitch `10.10.10.2` is static and is the reliable fallback when eth0 is down.)
- Note: the remote-access path now goes over Tailscale; this LAN-side sshd remains password-auth and unchanged.

### Known Issues

- Hyper-V VM reboot has caused temporary loss of keyboard responsiveness and SSH access. VM recovered after restart.
- **Host restart (distinct from a VM reboot) used to leave the VM with no internet and Tailscale offline** — RESOLVED 2026-06-18 via `AutomaticStopAction ShutDown` (see Remote Access → Host-restart connectivity). If it ever recurs before the External-vSwitch migration: get in via eth1 (`ssh klaw@10.10.10.2`) or vmconnect, then `sudo reboot` the guest.

### Planned Hardening (not yet completed)

- **Configure SSH keys — primarily for the WINDOWS hosts** (the VMs already need no keys; Tailscale SSH handles their auth). Per Windows host: generate a keypair on the client; place the PUBLIC key in `C:\ProgramData\ssh\administrators_authorized_keys` for ADMIN accounts (single shared file, strict perms — Administrators + SYSTEM only), or `C:\Users\<user>\.ssh\authorized_keys` for a non-admin account; then set `PasswordAuthentication no` in `C:\ProgramData\ssh\sshd_config` and restart sshd. This removes the password-every-time annoyance on Windows and sidesteps the Microsoft-account-credential issue.
- Disable password authentication after key verification. (Tailscale SSH already removes password need on the VM remote-access path; the LAN-side sshd password exposure on internal Hyper-V switches is a separate pre-existing item — optionally firewall it to the OllamaSwitch/Default-Switch subnet.)
- **Finish RustDesk lockdown on amethyst (5090) / rincon (NUC) / wren (Surface Go 2)** (direct-IP + inbound firewall scope to `$tailnet`); close the IPv4/IPv6 gap if desired; consider RustDesk "Use IP whitelisting" as app-level defense-in-depth.
- **Tailscale ACLs** as the cleaner tailnet-wide access control: one policy in the admin console gating e.g. `pacifico:21118` to a specific device set, applied to every node from a single edit, no per-host firewall commands and no risk of cutting a live session. Complements (doesn't replace) host firewall rules — ACLs gate what can route to the port, the host firewall gates what the OS accepts; run both for defense in depth.
- **Smart-plug remote-recovery backstop** (see Remote Access).
- Enable UFW firewall.
- Verify startup persistence of all OpenClaw services.
- Configure OpenClaw owner account.
- Configure execution approval policies.

***

## OpenClaw Gateway

- Service: systemd user service (`openclaw-gateway.service`)
- Status: active/running
- Port: 18789
- Bind mode: loopback only (127.0.0.1)
- Dashboard: <http://127.0.0.1:18789/>
- Connectivity probe: OK

### Gateway Restart Procedure

```
openclaw gateway restart
openclaw gateway status
```

Gateway restart is required after profile changes. This is a validated operational procedure.

***

## Telegram Channel

- Telegram bot configured and paired successfully.
- Remote conversations working via Telegram → OpenClaw Gateway. (Works because the VM makes an OUTBOUND connection to Telegram's servers — no inbound reachability needed. This is why Telegram worked before any inbound path like SSH/Tailscale existed. Telegram → Klaw is conversational only; Klaw still cannot execute CLI commands until the controlled-execution framework exists.)
- Web searches can be performed remotely through Telegram.
- Status: operational milestone achieved (June 11, 2026).

### Supported Channels (from OpenClaw)

OpenClaw natively supports: telegram, whatsapp, discord, irc, googlechat, slack, signal, imessage, feishu, nostr, msteams, mattermost, nextcloud-talk, matrix, line, zalo, clickclack, zalouser, sms, synology-chat, tlon, qa-channel, qqbot, twitch

***

## Windows Host Inventory & Licensing (discussed 2026-06-16/17; identities + 5090 edition updated 2026-06-20)

Relevant because both Hyper-V and hosting RDP require Windows Pro (Home has neither).

| Machine                 | Tailnet node | Edition                                               | Role                                                                                                                                                                                                                                                      |
| ----------------------- | ------------ | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3090 system             | `pacifico`   | Pro                                                   | Current Hyper-V host (klaw-machine); RustDesk host (Windows RDP disabled 2026-06-20).                                                                                                                                                                     |
| 5090 system             | `amethyst`   | **Pro (confirmed 2026-06-20)**                        | Intended future Hyper-V + OpenClaw host for the second node. Now on the tailnet. (Supersedes the earlier "OEM Home, needs Home→Pro upgrade" record — it is Pro now; whether upgraded or shipped Pro is unconfirmed but the Pro requirement is satisfied.) |
| Personal PC ("the NUC") | `rincon`     | **Pro — RETAIL channel** (confirmed via `slmgr /dli`) | Daily-driver PC. Retail = transferable. No firmware-embedded OEM license (`OA3xOriginalProductKey` returned blank).                                                                                                                                       |
| Surface Go 2 (refurb)   | `wren`       | Pro                                                   | SSH/RustDesk client terminal for managing GPU nodes. Client only.                                                                                                                                                                                         |

### Licensing decision analysis (2026-06-17) — now largely MOOT for the 5090

- **The 5090 (**`amethyst`**) is now Pro (confirmed 2026-06-20),** so the Home→Pro upgrade question and the "shuffle the NUC's retail Pro" analysis below no longer block the 5090's host role. Retained for reference / future machines.
- **OEM vs retail:** OEM licenses are locked to the motherboard (non-transferable); retail licenses are transferable. The Surface Go's Pro (OEM) cannot move. The NUC's Pro is **RETAIL**, so it CAN legally move.
- **The catch that killed the free "switcharoo":** moving the NUC's retail Pro to the 5090 would have left the NUC with NO license (its `OA3xOriginalProductKey` is blank = no firmware-embedded Home to fall back to). Unactivated Windows locks personalization, nags, and restricts some settings — unacceptable for a daily driver. (No longer relevant since the 5090 is already Pro.)
- If ever doing a Home→Pro edition flip that balks on a key: the generic public Pro upgrade key `VK7JG-NPHTM-C97JM-9MPGT-3V66T` changes EDITION only (does not activate), after which you activate with a real license.
- This is licensing terms, not legal advice; confirm edge cases with Microsoft.

***

## VM Resource Allocation & Multi-Node Seeding (design — 2026-06-16/17)

### Allocation philosophy: lean capable VM, fat host

The LLMs run on the HOST (Ollama on Windows), not in the VM. The VM runs OpenClaw orchestration, the gateway, Claude Code, scripts — a CPU/RAM workload, much lighter than model serving. Plus future ML wants the host's GPU/RAM/disk. So the split is NOT 50/50: give the VM ENOUGH, keep the bulk host-side.

### Memory: STATIC, not Dynamic (decided)

- **Use static (fixed) memory assignment.** Brian tested Dynamic Memory: gave the VM 16GB max but it ran at \~4-5GB and CRAWLED; disabling Dynamic Memory fixed it. This is a known Dynamic Memory failure mode — it optimizes for VM DENSITY (many VMs per host), not for a single VM that wants its working set resident, and its growth is reactive/lagging, worsened by cruder pressure signals from a Linux guest. Brian's contention worry is also valid: ballooning means host/guest negotiate "free" RAM, and reclaiming under host pressure is slow and can thrash — bad next to Ollama's big VRAM-resident models and future ML. Static is more predictable and correct here.
- Starting figure (pending actual host RAM totals): \~16GB static to klaw-machine is a comfortable ceiling for OpenClaw + Claude Code + tooling; bump if heavy in-VM work (local vector DB, big RAG indexing) is added.

### Disk: FIXED VHDX, not dynamic (revised toward fixed)

- Dynamic VHDX risks: write-perf overhead while expanding, fragmentation, and the nasty overcommit failure — a dynamic disk with a max larger than the host's real free space lets the guest think it has room, then the HOST runs out of physical disk mid-expansion = hard crash, not graceful "disk full." That's the disk analog of the RAM-contention worry, and it's real.
- **Fixed-size VHDX** avoids all of it (allocated upfront, best perf, no expansion surprise) at the cost of consuming full size on day one. For a workhorse VM on a box where Brian controls the disk budget, fixed is the defensible choice, same logic as static RAM. Suggested \~150-250GB (footprint is small now — OpenClaw, 684-page docs mirror, sessions, Claude Code, logs — but grows; size generously since growing later is painful).

### vCPU / GPU

- vCPUs: a chunk but not all (\~4-8 on a many-core host). OpenClaw isn't CPU-bound; over-allocating adds host scheduling contention.
- GPU: the VM does NOT touch the GPU by default, which is CORRECT here — Ollama on the host owns the 3090/5090 fully. Do NOT do GPU partitioning/passthrough to the guest unless specifically running GPU work inside it (would steal VRAM from the models). Keep the GPU host-side. Future ML reinforces this.

### Multi-node seeding: clone the VHDX, don't rebuild (design)

- Once klaw-machine is dialed in, seed the 5090's VM by COPYING the VHDX rather than reinstalling from scratch — a Hyper-V VM disk is just a `.vhdx`; clone it, create a new VM pointing at the copy = identical OpenClaw install (OS, Ollama config, OpenClaw, Claude Code, docs mirror, all of it).
- Make it repeatable: get klaw-machine to a known-good state, take a checkpoint, then export/copy the VHDX as a "golden image" — also doubles as disaster-recovery baseline. Copy from a SHUT-DOWN VM (or clean checkpoint) for a consistent image.
- **Identity-collision steps required on the clone** (learned-relevant: Brian saw firsthand how duplicate Tailscale nodes cause confusion): rename the host (don't run a second `klaw-machine`); regenerate SSH host keys; log the clone into Tailscale FRESH (`sudo tailscale up --ssh`) so it registers as its OWN node; and repoint the clone's Ollama endpoint at the 5090 host's OllamaSwitch IP, not the 3090's.
- **Substrate vs specialization:** the clone is "skip reinstalling the boring 90%," NOT "duplicate Klaw." The two instances then diverge (agent configs, model assignments, roles, responsibilities) — see the Multi-Node Co-Orchestration design in the Model Strategy & Orchestration note for the divide-and-conquer-vs-specialize axis and the chain-of-command design.

***

## VM Administration

### Checkpoints

A Hyper-V checkpoint named "Solved Openclaw Performance Issue - 6/11/2026 1:01 AM EDT" exists and captures a known-good state. (See the Checkpoints & Change Log note for the full VM Snapshot Registry — later snapshots also exist.)

### Automatic Start/Stop Actions (set 2026-06-18)

- APPLIED + VERIFIED 2026-06-18 (`Get-VM` on host): `AutomaticStopAction = ShutDown`, `AutomaticStartAction = Start`, `AutomaticStartDelay = 30`. Was `Save` / `StartIfRunning` / `0`.
- Reason: the old `Save` action triggered the save/resume that broke eth0 on host restart (see Remote Access → Host-restart connectivity). `ShutDown` forces a clean guest power-off on host shutdown and a cold boot (fresh DHCP) on host start; the 30s delay lets the virtual switch initialize first.
- Apply procedure + gotchas (must power VM Off for `AutomaticStopAction`; cmdlets are host-only + need admin) are documented in the Host-restart connectivity section.

### Startup Persistence

- OpenClaw Gateway confirmed auto-starting via systemd user service.
- `tailscaled` confirmed `enabled` + auto-starting (2026-06-18). NOTE: daemon auto-start ≠ Tailscale connectivity after a host restart — see Host-restart connectivity (now mitigated by the `ShutDown` action forcing a fresh lease on cold boot).
- Verification after reboots is recommended.

***

## Future Networking Work

### Default Switch → External vSwitch (recommended, raised 2026-06-18)

- The NAT Default Switch is the weak link: it rebuilds on a new subnet across host reboots (causing both the changing-eth0-IP annoyance and — before the `ShutDown` fix — the host-restart Tailscale outage). Replacing it with an External vSwitch bridged to the host's physical NIC gives eth0 a normal router lease (stable subnet, real ARP-answering gateway). With `AutomaticStopAction ShutDown` now applied the outage is already prevented; the External vSwitch remains the cleaner structural fix and would also stabilize the eth0 IP. Bigger change; stage deliberately.

### Multi-node networking: 3090 ↔ 5090 (discussed 2026-06-16 — no decisions made)

- **Direct Ethernet cable between the two hosts:** physically works (modern NICs have Auto-MDI-X, no crossover cable needed), but not plug-and-play — with no DHCP on a 2-PC link, both ends self-assign useless 169.254.x.x addresses, so you must set static IPs manually on each end (same pattern as the OllamaSwitch static config). Downside: isolated host-to-host link only; doesn't extend to the VMs or other devices.
- **Better local option:** a cheap gigabit switch → router puts all machines on one LAN with automatic addressing + internet. A dedicated fast host-to-host NIC+cable can be added later purely for node-to-node VM traffic. (A 2.5GbE unmanaged switch was previously recommended for the 3090↔5090 link.)
- **Tailscale already covers host-to-host:** both the 3090 (`pacifico`) and the 5090 (`amethyst`) are now on the tailnet, reachable by `100.x.x.x` regardless of physical wiring.
- **The real open work = VM-to-VM:** Tailscale on the hosts does NOT automatically bridge the two OpenClaw VMs (they sit behind each host's Hyper-V switches). Options: (a) install Tailscale INSIDE each VM (cleanest — each VM its own tailnet node), or (b) Tailscale subnet routing on each host advertising the VM subnets.
- Decisions deferred until the 5090's OpenClaw VM physically exists.

### Other

- External exposure of OpenClaw's own gateway (currently loopback only) — deferred pending security hardening.
- Tailscale exposure of the OpenClaw GATEWAY remains disabled in OpenClaw's own config. (Distinct from the personal-use Tailscale installed on the host/VM for SSH/RustDesk — that is the user's own access layer, not OpenClaw exposing its gateway.)

***

## Recent Updates

- 2026-06-13: Networking note created from legacy source consolidation.
- 2026-06-16: Added Remote Access section. Tailscale mesh established (host, VM, phone) on `bmills85@`. VM SSH via Tailscale SSH VERIFIED passwordless. Windows host OpenSSH installed/running. Recorded native-RDP-over-Tailscale plan, Windows licensing/OEM-vs-retail discussion, and the 3090↔5090 networking discussion.
- 2026-06-17: Surface Go 2 received. Long remote-access debugging session resolved: (1) intermittent phone-SSH hang (transient; also changed Tailscale SSH ACL `check`→`accept`); (2) Windows SSH "wrong password" = wrong USERNAME (Microsoft-account logins need the short local username, not email/PIN) — the durable lesson. Tailnet grew to 5 nodes. Laptop OpenSSH install underway (typo `OpenSHH` caught). Confirmed NUC = RETAIL Pro (transferable) with no firmware-embedded license. Added VM Resource Allocation & Multi-Node Seeding design section.
- 2026-06-18: Diagnosed AND fixed "Tailscale offline after host restart." Root cause CONFIRMED = Hyper-V save/resume (default `AutomaticStopAction Save`) leaving the resumed guest with a dead eth0 route after the NAT Default Switch rebuilt on a new subnet (`192.168.96.x` → `172.28.96.x` observed) — tailscaled itself was healthy/enabled the whole time (2-day uptime spanned the restart). Immediate fix: cold `sudo reboot` of the guest. Durable fix APPLIED + VERIFIED on host: `AutomaticStopAction = ShutDown`, `AutomaticStartAction = Start`, `AutomaticStartDelay = 30`. Gotchas logged. Recommended structural cure (not done): External vSwitch. Recorded observed tailnet node renames.
- 2026-06-20: **Remote-desktop layer switched from native RDP to RustDesk over Tailscale.** Windows RDP fully DISABLED on pacifico (`fDenyTSConnections=1`, "Remote Desktop" firewall rules disabled, `TermService` StartupType `Disabled`; 3389 listener confirmed gone). Reason: closing a Windows RDP session was tied to the GPU-no-video hard-wedge hit physically (powered on, no signal, needed forced power-cycle at BIOS); RDP's session teardown on disconnect hands the console back to the GPU, while RustDesk attaches to the existing console session with no teardown. RustDesk direct-IP enabled on pacifico (port 21118; `netstat` confirms LISTENING on `0.0.0.0:21118` AND `[::]:21118`, PID 8460). Inbound `RustDesk Service` firewall rules (two, program-allow) scoped to the 6 tailnet IPv4 addresses; outbound left `Any` (relay fallback intact). Two PowerShell gotchas logged: `-DisplayName`+`-Direction` is `AmbiguousParameterSet` on `Get-NetFirewallRule` (filter with `Where-Object`); and — the big one — `$tailnet` was empty across a new session, and `Set-NetFirewallRule -RemoteAddress $null` silently resolves to `Any`, so earlier "successful" scopes were silent no-ops (fix: redefine in-session + `if ($tailnet.Count -lt 6){throw}` guard). KNOWN GAP: firewall allow-list is IPv4-only while the listener is also on IPv6 `[::]:21118` (Tailscale `fd7a:115c:a1e0::/48`). Idle sleep was checked and ruled out (power plan = Never on AC) and the Application-API sleep log entries were benign (each resumed cleanly) — no further action there. **Node identities CONFIRMED** (resolves the long-standing laptop-vs-NUC TBC): `amethyst` = the 5090 system (Windows 11 Pro, now on the tailnet — supersedes the earlier "5090 = OEM Home" record); `rincon` = the NUC (personal daily driver); `wren` = the Surface Go 2; `pacifico` = 3090 host; `bovinius` = phone. amethyst/rincon/wren still need RustDesk direct-IP + firewall scoping — to be done remotely over the relay. Smart-plug remote-recovery backstop (BIOS "Restore on AC Power Loss → Power On") remains the recommended way out of a hard hang; not yet implemented.
