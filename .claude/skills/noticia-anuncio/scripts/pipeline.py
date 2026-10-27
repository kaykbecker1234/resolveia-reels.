#!/usr/bin/env python3
"""Pipeline notícia -> anúncio. Uso (de qualquer pasta):

  python3 pipeline.py check   <pasta>          valida roteiro.json e imprime o texto para a voz
  python3 pipeline.py preview <pasta>          gera <pasta>/preview.jpg (12 quadros)
  python3 pipeline.py voz     <pasta> <url>    baixa a narração do ElevenLabs para <pasta>/voz.mp3
  python3 pipeline.py final   <pasta> [...]    sincroniza, renderiza, mixa e gera <pasta>/<nome>.mp4 + sync.jpg

A pasta precisa ter roteiro.json (ver assets/exemplo/roteiro.json). Saída sempre curta, de propósito.
"""
import difflib, hashlib, json, os, re, shutil, subprocess, sys, unicodedata, wave

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(SKILL, "scripts", "render.js")
CACHE = os.path.expanduser("~/.cache/noticia-anuncio")
VENV = os.path.join(CACHE, "venv")
VPY = os.path.join(VENV, "bin", "python")
SR = 44100

REQUIRED = ["fonte", "data_curta", "s1.l1", "s1.empresa", "s1.de", "s1.para", "s1.tarja",
            "s2.r1_rotulo", "s2.r1_valor", "s2.r1_txt", "s2.r2_rotulo", "s2.r2_valor", "s2.r2_txt", "s2.q1", "s2.q2",
            "s4.msgs", "s5.contato", "s5.msg", "s6.m1", "s6.m2", "s6.tiles", "s6.m3", "s6.m4", "s6.pills",
            "s7.st1_num", "s7.st1_a", "s7.st1_b", "s7.st2_num", "s7.st2_txt", "s7.st2_a", "s7.st2_b"]


# ---------- ambiente ----------
def ensure_venv():
    if os.path.abspath(sys.prefix) == os.path.abspath(VENV):
        return
    if not os.path.exists(VPY):
        print("[setup] criando ambiente (só na primeira vez)…", flush=True)
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
        subprocess.run([VPY, "-m", "pip", "install", "-q", "numpy", "faster-whisper", "num2words"], check=True)
    os.execv(VPY, [VPY] + sys.argv)


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"ERRO: {' '.join(map(str, cmd[:3]))}…\n{r.stderr[-1500:]}")
    return r.stdout


def load(d):
    return json.load(open(os.path.join(d, "roteiro.json"), encoding="utf-8"))


def meta(d):
    return json.loads(sh(["node", RENDER, "meta", os.path.join(d, "roteiro.json")]))


def get(o, path):
    for k in path.split("."):
        o = o.get(k) if isinstance(o, dict) else None
    return o


# ---------- check ----------
def cmd_check(d):
    r, m = load(d), meta(d)
    tela, nar = r.get("tela", {}), r.get("narracao", [])
    errs = [f"falta tela.{p}" for p in REQUIRED if get(tela, p) in (None, "", [])]
    order = list(m["marks"])
    got = [s.get("m") for s in nar]
    if got != order:
        errs.append(f"narracao: as marcas precisam ser exatamente, nesta ordem: {' '.join(order)}")
    if len(tela.get("s6", {}).get("pills", [])) != 4: errs.append("tela.s6.pills precisa de 4 itens")
    if len(tela.get("s4", {}).get("msgs", [])) != 4: errs.append("tela.s4.msgs precisa de 4 itens [texto, hora]")
    if len(tela.get("s6", {}).get("tiles", [])) != 3: errs.append("tela.s6.tiles precisa de 3 itens")
    text = " ".join(s.get("t", "").strip() for s in nar)
    if re.search(r"\d", text): errs.append("narracao tem algarismos: escreva números por extenso")
    words = len(text.split())
    est = words / 3.2 + 3.5
    if errs:
        print("PROBLEMAS:\n- " + "\n- ".join(errs))
        sys.exit(1)
    warn = "  (ACIMA de 60s: enxugue)" if est > 60 else ""
    print(f"OK · {words} palavras · ~{est:.0f}s{warn}\n--- TEXTO PARA A VOZ ---\n{text}")


# ---------- preview ----------
def tile(src_glob_dir, out, labels=None):
    files = sorted(f for f in os.listdir(src_glob_dir) if f.endswith(".jpg"))
    inputs, filt = [], []
    for i, f in enumerate(files):
        inputs += ["-i", os.path.join(src_glob_dir, f)]
        lab = f",drawtext=text='{labels[i]}':fontcolor=yellow:fontsize=26:x=8:y=8:box=1:boxcolor=black@0.5" if labels else ""
        filt.append(f"[{i}]scale=270:480{lab}[v{i}]")
    n = len(files)
    filt.append("".join(f"[v{i}]" for i in range(n)) + f"xstack=inputs={n}:layout=" +
                "|".join(f"{(i % 6) * 270}_{(i // 6) * 480}" for i in range(n)) + "[o]")
    sh(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filt), "-map", "[o]", "-frames:v", "1", out])
    shutil.rmtree(src_glob_dir)


def cmd_preview(d):
    out = os.path.join(d, "preview.jpg")
    prev = sh(["node", RENDER, "preview", os.path.join(d, "roteiro.json"), out]).strip()
    tile(prev, out)
    print(out)


# ---------- voz ----------
def cmd_voz(d, url):
    sh(["curl", "-sSfL", "-o", os.path.join(d, "voz.mp3"), url])
    print(os.path.join(d, "voz.mp3"))


# ---------- alinhamento ----------
def num_words(s):
    from num2words import num2words
    s = s.replace(".", "") if re.fullmatch(r"\d{1,3}(\.\d{3})+", s) else s.replace(",", ".")
    v = float(s)
    return num2words(int(v) if v.is_integer() else v, lang="pt_BR")


def tokens(text):
    t = text.lower()
    t = re.sub(r"(?<=\w)\.(?=\w)", "", t)
    t = re.sub(r"(\d[\d.,]*)\s*%", lambda m: num_words(m.group(1).rstrip(".,")) + " por cento", t)
    t = re.sub(r"\d[\d.,]*", lambda m: num_words(m.group(0).rstrip(".,")), t)
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def transcribe(wav16):
    import numpy as np
    from faster_whisper import WhisperModel
    a = np.fromfile(wav16, dtype=np.float32)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(a, language="pt", word_timestamps=True)
    toks = []
    for s in segs:
        for w in s.words:
            tk = tokens(w.word)
            for j, x in enumerate(tk):
                f = (w.end - w.start) / max(1, len(tk))
                toks.append((x, w.start + j * f, w.start + (j + 1) * f))
    return toks


def align(d, r, m, tempo):
    out = os.path.join(d, "_work")
    os.makedirs(out, exist_ok=True)
    voice = os.path.join(out, "voice.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, "voz.mp3"), "-af", f"atempo={tempo}", "-ar", str(SR), "-ac", "1", voice])
    w16 = os.path.join(out, "v16.f32")
    sh(["ffmpeg", "-v", "error", "-y", "-i", voice, "-ac", "1", "-ar", "16000", "-f", "f32le", w16])
    tr = transcribe(w16)
    os.remove(w16)
    nar = r["narracao"]
    st, seg_of = [], []
    for i, s in enumerate(nar):
        tk = tokens(s["t"])
        seg_of.append(len(st))
        st += tk
    tt = [x[0] for x in tr]
    mp = {}
    for a, b, n in difflib.SequenceMatcher(None, st, tt, autojunk=False).get_matching_blocks():
        for k in range(n):
            mp[a + k] = b + k
    times, warns = [], []
    for i, s0 in enumerate(seg_of):
        s1 = seg_of[i + 1] if i + 1 < len(seg_of) else len(st)
        t = None
        for k in range(min(5, s1 - s0)):
            if s0 + k in mp:
                t = tr[mp[s0 + k]][1] - k * 0.22
                break
        times.append(t)
    known = [(seg_of[i], t) for i, t in enumerate(times) if t is not None]
    for i, t in enumerate(times):
        if t is None:
            warns.append(nar[i]["m"])
            lo = max((k for k in known if k[0] < seg_of[i]), default=(0, 0.0))
            hi = min((k for k in known if k[0] > seg_of[i]), default=(len(st), tr[-1][2]))
            times[i] = lo[1] + (hi[1] - lo[1]) * (seg_of[i] - lo[0]) / max(1, hi[0] - lo[0])
    last_end = tr[-1][2]
    marks, scenes = m["marks"], set(m["scenes"])
    anchors = [(0.0, 0.0)]
    for s, t in zip(nar, times):
        b = marks[s["m"]]
        if b == 0:
            continue
        if s["m"] in scenes and b - 0.6 > anchors[-1][0] + .05 and t - 0.6 > anchors[-1][1] + .05:
            anchors.append((b - 0.6, t - 0.6))
        if t <= anchors[-1][1] + 0.05:
            warns.append(f"{s['m']}(apertado)")
            t = anchors[-1][1] + 0.15
        anchors.append((b, t))
    tail = max(anchors[-1][1] + 0.9, last_end + 0.3)
    anchors.append((m["tail"], tail))
    dur = tail + (m["end"] - m["tail"]) * 0.8
    anchors.append((m["end"], dur))
    timing = {"tempo": tempo, "duration": round(dur, 3), "anchors": anchors,
              "cues": {s["m"]: round(t, 3) for s, t in zip(nar, times)}}
    json.dump(timing, open(os.path.join(out, "timing.json"), "w"))
    return timing, voice, warns


# ---------- efeitos sonoros (sintetizados, sem créditos) ----------
def sfx_bank():
    import numpy as np
    bank_dir = os.path.join(CACHE, "sfx")
    names = ["whoosh", "whoosh_long", "impact", "pop", "click", "tick", "ding", "riser", "glitch", "swipe", "bubble", "send"]
    if all(os.path.exists(os.path.join(bank_dir, n + ".npy")) for n in names):
        return {n: np.load(os.path.join(bank_dir, n + ".npy")) for n in names}
    os.makedirs(bank_dir, exist_ok=True)
    rng = np.random.default_rng(7)
    T = lambda d: np.arange(int(SR * d)) / SR

    def lp(x, fc):
        fc = np.broadcast_to(np.asarray(fc, float), x.shape); a = np.exp(-2 * np.pi * fc / SR)
        y = np.empty_like(x); s = 0.0
        for i in range(len(x)):
            s = (1 - a[i]) * x[i] + a[i] * s; y[i] = s
        return y

    hp = lambda x, fc: x - lp(x, fc)
    sine = lambda f: np.sin(2 * np.pi * np.cumsum(f) / SR)

    def whoosh(d=.45, f0=300, f1=4000):
        n = int(SR * d); return hp(lp(rng.standard_normal(n), np.geomspace(f0, f1, n)), 150) * np.sin(np.linspace(0, np.pi, n)) ** 1.5

    def impact():
        t = T(1.2); return sine(38 + 70 * np.exp(-t * 18)) * np.exp(-t * 3.2) + .5 * lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 40)

    def ding():
        t = T(.7); x = np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 7); o = int(SR * .09)
        x[o:] += (np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 6))[:len(t) - o]; return x

    def riser(d=1.4):
        t = T(d); return (.35 * sine(np.geomspace(180, 1400, len(t))) + .8 * lp(rng.standard_normal(len(t)), np.geomspace(400, 7000, len(t)))) * np.linspace(0, 1, len(t)) ** 2

    def glitch(d=.45):
        n = int(SR * d); x = np.zeros(n); p = 0
        while p < n:
            L = int(SR * rng.uniform(.01, .05))
            seg = np.sign(np.sin(2 * np.pi * rng.uniform(80, 900) * np.arange(L) / SR)) * rng.uniform(.3, 1)
            if rng.random() < .35: seg = rng.standard_normal(L) * .6
            x[p:p + L] = seg[:max(0, min(L, n - p))]; p += L + int(SR * rng.uniform(0, .02))
        e = np.ones(n); e[:220] = np.linspace(0, 1, 220); e[220:] = np.linspace(1, 0, n - 220); return lp(x, 6000) * e

    t = T
    bank = {"whoosh": whoosh(), "whoosh_long": whoosh(.7, 200, 3000), "impact": impact(),
            "pop": sine(900 * np.exp(-t(.09) * 25) + 250) * np.exp(-t(.09) * 45),
            "click": hp(rng.standard_normal(len(t(.025))), 2000) * np.exp(-t(.025) * 260),
            "tick": (np.sin(2 * np.pi * 2400 * t(.03)) + .4 * hp(rng.standard_normal(len(t(.03))), 3000)) * np.exp(-t(.03) * 180),
            "ding": ding(), "riser": riser(), "glitch": glitch(), "swipe": whoosh(.3, 800, 6000) * .8,
            "bubble": sine(500 + 900 * t(.12) / .12) * np.exp(-t(.12) * 30),
            "send": sine(np.geomspace(500, 1500, len(t(.25)))) * np.exp(-t(.25) * 14) + .3 * whoosh(.25, 2000, 8000)}
    for k, v in bank.items():
        v = v / (np.max(np.abs(v)) + 1e-9) * .9
        np.save(os.path.join(bank_dir, k + ".npy"), v); bank[k] = v
    return bank


def decode(path):
    import numpy as np
    raw = sh_bytes(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
    return np.frombuffer(raw, np.float32).astype(np.float64)


def sh_bytes(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode: sys.exit(f"ERRO ffmpeg: {r.stderr[-800:]}")
    return r.stdout


def write_wav(path, x):
    import numpy as np
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def mix(d, r, m, timing, voice):
    import numpy as np
    out = os.path.join(d, "_work")
    A = timing["anchors"]

    def b2f(v):
        for (a0, b0), (a1, b1) in zip(A, A[1:]):
            if v <= a1: return b0 + (b1 - b0) * max(0, v - a0) / (a1 - a0)
        return A[-1][1]

    n = int(timing["duration"] * SR)
    bank, sfx = sfx_bank(), np.zeros(n + SR * 2)
    for v, name, g in m["sfx"]:
        s = bank[name]; i = int(b2f(v) * SR); sfx[i:i + len(s)] += s[:max(0, len(sfx) - i)] * g
    write_wav(os.path.join(out, "sfx.wav"), sfx[:n])
    mus_dir = os.path.join(SKILL, "assets", "musicas")
    lib = sorted(f for f in os.listdir(mus_dir) if f.endswith(".mp3"))
    pick = r.get("audio", {}).get("musica") or lib[int(hashlib.md5(os.path.basename(os.path.abspath(d)).encode()).hexdigest(), 16) % len(lib)]
    mu = decode(os.path.join(mus_dir, pick))
    while len(mu) < n:
        xf, cut = 2 * SR, len(mu) // 2
        f = np.linspace(0, 1, xf)
        mu = np.concatenate([mu[:-xf], mu[-xf:] * (1 - f) + mu[cut:cut + xf] * f, mu[cut + xf:]])
    mu = mu[:n].copy(); fo = int(2.5 * SR); mu[-fo:] *= np.linspace(1, 0, fo)
    write_wav(os.path.join(out, "music.wav"), mu)
    vol = r.get("audio", {}).get("musica_vol", 0.10)
    final = os.path.join(out, "mix.wav")
    sh(["ffmpeg", "-v", "error", "-y", "-i", voice, "-i", os.path.join(out, "music.wav"), "-i", os.path.join(out, "sfx.wav"),
        "-filter_complex", f"[0]asplit=2[v][sc];[1]volume={vol}[m];[m][sc]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=500[md];"
        "[2]volume=0.9[s];[v][md][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[o]",
        "-map", "[o]", "-ar", str(SR), "-ac", "2", final])
    return final, pick


# ---------- final ----------
def cmd_final(d):
    r, m = load(d), meta(d)
    if not os.path.exists(os.path.join(d, "voz.mp3")):
        sys.exit("falta voz.mp3 (use: pipeline.py voz <pasta> <url>)")
    tempo = r.get("audio", {}).get("tempo", 1.08)
    timing, voice, warns = align(d, r, m, tempo)
    work = os.path.join(d, "_work")
    frames = os.path.join(work, "frames")
    tj = os.path.join(work, "timing.json")
    sh(["node", RENDER, "frames", os.path.join(d, "roteiro.json"), tj, frames, str(r.get("workers", 3))])
    audio, music = mix(d, r, m, timing, voice)
    name = os.path.basename(os.path.abspath(d))
    mp4 = os.path.join(d, name + ".mp4")
    sh(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", os.path.join(frames, "f_%05d.jpg"), "-i", audio,
        "-c:v", "libx264", "-preset", "medium", "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4])
    shutil.rmtree(frames)
    keys = ["s1_para", "s2_q", "s3", "s4_p1", "s5_b", "s6", "s6_p3", "s7_st2", "s7_card", "s8_q2", "s9", "s9_c"]
    sd = os.path.join(work, "_sync"); os.makedirs(sd, exist_ok=True)
    for i, k in enumerate(keys):
        sh(["ffmpeg", "-v", "error", "-y", "-ss", str(timing["cues"][k] + 0.8), "-i", mp4, "-frames:v", "1", os.path.join(sd, f"{i:02d}.jpg")])
    tile(sd, os.path.join(d, "sync.jpg"), keys)
    for f in ("voice.wav", "music.wav", "sfx.wav", "mix.wav"):
        os.remove(os.path.join(work, f))
    mb = os.path.getsize(mp4) / 1e6
    print(f"OK {mp4} · {timing['duration']:.1f}s · {mb:.0f}MB · música {music}" + (f" · conferir marcas: {', '.join(warns)}" if warns else ""))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd in ("final",):
        ensure_venv()
    if cmd == "check": cmd_check(args[0])
    elif cmd == "preview": cmd_preview(args[0])
    elif cmd == "voz": cmd_voz(args[0], args[1])
    elif cmd == "final":
        for d in args: cmd_final(d)
    else: sys.exit(__doc__)
