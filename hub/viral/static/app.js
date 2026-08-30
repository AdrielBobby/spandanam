// Thaalam dashboard — ES module, no bundler. Ported from the old single-file index.html
// plus: kaalam ladder, motion coach, vaaythari karaoke chip, and a three.js chenda stage
// (gracefully degrading to the existing DOM-only falling-note UI if WebGL/the model fails).

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// ── constants ──────────────────────────────────────────────────────────
const COLORS = ["#ff3b30", "#ff9500", "#ffd60a", "#34c759", "#0a84ff"];
const NAMES = ["thumb", "index", "middle", "ring", "pinky"];
const NAMES_ML = ["തള്ളവിരൽ", "ചൂണ്ടുവിരൽ", "നടുവിരൽ", "മോതിരവിരൽ", "ചെറുവിരൽ"];
const KEYLBL = ["SPACE", "J", "K", "L", ";"];
const FINGER_TO_KEY = [" ", "j", "k", "l", ";"];
const KEYS = { " ": 0, j: 1, k: 2, l: 3, ";": 4 };
const DEFAULT_SCALES = [0.6, 0.8, 1.0, 2.0]; // display default only — server re-defaults if omitted

const $ = (s) => document.querySelector(s);

let ws, state = {}, score = null, play = null;
let fmap = { names: NAMES, syllables: ["", "", "", "", ""] };
let mode = "free";
let ladder = null; // {total, step, scale}

// ── say(): single write-path into #asan ──────────────────────────────
let asanTimer = null, lastAsan = "";
const ASAN_IDLE = `<div class="mlbig">ആശാൻ തയ്യാർ</div><div class="en">Asan is listening. Play a round and I'll tell you what to fix — tempo, timing, which finger is drifting.</div>`;
function say(html, { ms = 6000 } = {}) {
  lastAsan = html;
  $("#asanBody").innerHTML = html;
  $("#asan").classList.add("show");
  clearTimeout(asanTimer);
  asanTimer = setTimeout(hideAsan, ms);
}
function hideAsan() { clearTimeout(asanTimer); $("#asan").classList.remove("show"); }
$("#asanClose").onclick = hideAsan;
// Asan is otherwise invisible until a coach message arrives — which needs a finished round
// AND a reachable Gemma. The rail button makes him always available and replays the last thing he said.
$("#asanBtn").onclick = () =>
  $("#asan").classList.contains("show") ? hideAsan() : say(lastAsan || ASAN_IDLE, { ms: 9000 });

// ── mode / rig badges ──────────────────────────────────────────────────
function setMode(m) {
  mode = m;
  $("#mode").textContent = m;
}

// ── #foot: finger/key chips (replaces old .pad) ────────────────────────
function renderFoot() {
  $("#foot").innerHTML = NAMES.map((n, i) => `
    <div class="fchip" id="f${i}" data-finger="${i}" style="border-color:${COLORS[i]};color:${COLORS[i]}">
      <span class="key">${KEYLBL[i]}</span>
      <b>${fmap.names[i] || n}</b>
      <small>${fmap.syllables[i] || "—"}</small>
      <span class="mln ml">${NAMES_ML[i]}</span>
    </div>`).join("");
  document.querySelectorAll("#foot .fchip").forEach((el) => {
    el.addEventListener("pointerdown", () => sendStrike(+el.dataset.finger, 0.9, "pointer"));
  });
}
function flashFoot(i) {
  const el = $("#f" + i);
  if (!el) return;
  el.classList.add("hit");
  setTimeout(() => el.classList.remove("hit"), 80);
}

// ── unified strike input: keyboard, #foot pointer, and 3D raycast all call this ──
function sendStrike(finger, v = 0.9, src = "key") {
  ws.send(JSON.stringify({ type: "key", key: FINGER_TO_KEY[finger], v }));
  triggerStrikeFx(finger, src); // optimistic local ripple/shake, doesn't wait for the server round-trip
}

document.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  const k = e.key.toLowerCase();
  if (k in KEYS || e.key === " ") {
    e.preventDefault();
    sendStrike(KEYS[e.key === " " ? " " : k], 0.9, "key");
  }
});

// ── judge flash text ─────────────────────────────────────────────────
function judge(t, c) {
  const j = $("#judge");
  j.textContent = t; j.style.color = c; j.style.opacity = 1;
  setTimeout(() => (j.style.opacity = 0), 300);
}

// ── falling notes (#track) — timing math ported unchanged ──────────────
let notesEl = [];
function setScore(s) {
  score = s; fmap = s.finger_map; renderFoot();
  const ph = $("#phrase");
  ph.innerHTML = '<option value="">whole piece</option>' +
    (s.phrases || []).map((p, i) => `<option value="${i}">phrase ${i + 1} (beats ${p[0]}–${p[1]})</option>`).join("");
}
function startPractice(s, lead, isListen) {
  $("#verdict").style.display = "none"; $("#hint").style.display = "none";
  score = s; fmap = s.finger_map; renderFoot();
  $("#pts").textContent = 0; $("#streak").textContent = 0;
  notesEl.forEach((n) => n.remove()); notesEl = [];
  const t0 = performance.now() + lead * 1000, beat = 60000 / s.bpm;
  play = { t0, beat };
  s.notes.forEach((n, i) => {
    const el = document.createElement("div");
    el.className = "note";
    el.style.left = (n.finger * 20 + 2) + "%";
    el.style.background = COLORS[n.finger];
    el.dataset.t = t0 + n.beat * beat;
    el.textContent = (n.label || "").toUpperCase();
    el.title = n.label;
    $("#track").appendChild(el);
    notesEl.push(el);
  });
  build3DNotes(s);                     // mirror the same notes onto the 3D lanes
  setMode(isListen ? "listen" : "practice");
  scheduleKaraokeChip(lead);
}
function markNote(i, v) {
  const m = noteMeshes[i];
  if (m) m.userData.consumed = true;            // the 3D note has been played/missed — clear the lane
  const el = notesEl[i];
  if (!el) return;
  if (v === "auto") { el.style.boxShadow = "0 0 12px #fff"; setTimeout(() => (el.style.opacity = 0.25), 120); return; }
  el.style.opacity = 0.25;
  if (v === "miss" || v === "wrong_finger") el.style.background = "#333";
}
const APPROACH_MS = 2000;   // how long a note is visible before its beat lands
// CSS owns where the gold hit line sits (--hit); we read the element's real offset so
// notes always land exactly ON it. The old code hardcoded 96px (line) and -70px (notes)
// separately — leftovers from when the finger pad lived inside the stage — so notes
// stopped ~31px short of the line they were supposed to meet.
function hitLineY() {
  const line = $(".hitline");
  return line ? line.offsetTop : $("#track").clientHeight - 104;
}
function updateNotes(now) {
  if (!play) return;
  const hitY = hitLineY(), speed = hitY / APPROACH_MS;
  notesEl.forEach((el) => {
    const dt = +el.dataset.t - now;
    const y = hitY - dt * speed;                          // dt === 0 → dead on the line
    el.style.transform = `translate3d(0,${y - 13}px,0)`;  // 13 = half the note height
    el.style.visibility = (y < -30 || y > hitY + 90) ? "hidden" : "visible";
  });
}

// ── vaaythari karaoke chip: client-inferred from lead-in timing, no dedicated WS message ──
let chantChipTimer = null;
function scheduleKaraokeChip(leadInS) {
  clearHudChip("chant");
  if (!leadInS || leadInS <= 0) return;
  addHudChip("chant", "chant", "🎙 chant on");
  clearTimeout(chantChipTimer);
  chantChipTimer = setTimeout(() => clearHudChip("chant"), leadInS * 1000);
}

// ── #hud chips (kit/ladder/karaoke) ─────────────────────────────────────
function addHudChip(id, cls, text) {
  clearHudChip(id);
  const c = document.createElement("span");
  c.className = "chip " + cls; c.id = "hud-" + id; c.textContent = text;
  $("#hud").appendChild(c);
}
function clearHudChip(id) {
  const el = $("#hud-" + id);
  if (el) el.remove();
}

// ── kaalam ladder ────────────────────────────────────────────────────
function onLadderStart(m) {
  ladder = { total: m.total_steps, step: 0, scale: m.bpm_scale };
  renderLadderChip();
  $("#ladderInfo").textContent = `step 1 / ${ladder.total} · ×${ladder.scale}`;
  say(`<div class="mlbig">കാലം ഗോവണി തുടങ്ങി</div><div class="en">Kaalam ladder: step 1 of ${ladder.total}, ×${ladder.scale} tempo.</div>`);
}
function onLadderEvent(m, kind) {
  if (kind === "complete") {
    ladder = null;
    clearHudChip("ladder");
    $("#ladderInfo").textContent = "complete!";
    say(`<div class="mlbig">കാലം ഗോവണി പൂർത്തിയായി! 🎉</div><div class="en">Kaalam ladder complete — every tempo step passed.</div>`);
    return;
  }
  ladder = { total: m.total_steps, step: m.step, scale: m.bpm_scale };
  renderLadderChip();
  if (kind === "step_up") {
    $("#ladderInfo").textContent = `step ${ladder.step + 1} / ${ladder.total} · ×${ladder.scale}`;
    say(`<div class="mlbig">നന്നായി! അടുത്ത കാലം</div><div class="en">Nice — stepping up to ×${ladder.scale} tempo.</div>`);
  } else {
    $("#ladderInfo").textContent = `retry step ${ladder.step + 1} / ${ladder.total} · ×${ladder.scale}`;
    say(`<div class="mlbig">വീണ്ടും ശ്രമിക്കൂ</div><div class="en">Not quite — same tempo (×${ladder.scale}), try again.</div>`);
  }
}
function renderLadderChip() {
  if (!ladder) { clearHudChip("ladder"); return; }
  addHudChip("ladder", "gold", `kaalam ${ladder.step + 1}/${ladder.total} · ×${ladder.scale}`);
}

// ── #verdict: round-end stats + motion coach ────────────────────────────
function showVerdict(summary) {
  const s = summary;
  $("#vStars").textContent = "★".repeat(s.stars) + "☆".repeat(3 - s.stars);
  $("#vPts").textContent = s.points + " pts";
  $("#vLine").textContent = `${Math.round(s.accuracy * 100)}% · perfect ${s.perfect} · good ${s.good} · miss ${s.misses} · wrong ${s.wrong_finger}`;
  $("#vSub").textContent = s.stars >= 2 ? "കൊള്ളാം! · Ashaan is thinking…" : "വീണ്ടും ശ്രമിക്കൂ · Ashaan is thinking…";
  $("#summary").innerHTML = `${"★".repeat(s.stars)}${"☆".repeat(3 - s.stars)} &nbsp; ${Math.round(s.accuracy * 100)}% · ${s.points} pts<br>perfect ${s.perfect} · good ${s.good} · miss ${s.misses} · wrong finger ${s.wrong_finger}`;
  const vm = $("#vMotion");
  if (s.motion) {
    vm.classList.remove("hidden", "motion-good", "motion-flat");
    vm.classList.add("motion-" + s.motion.verdict);
    vm.textContent = `wrist: ${s.motion.verdict} · tilt ${s.motion.avg_tilt_deg}° · ${s.motion.avg_peak_g}g${s.motion.hint ? " — " + s.motion.hint : ""}`;
    if (s.motion.hint) say(`<div class="mlbig">${s.motion.verdict === "flat" ? "കൈത്തണ്ട ഉയർത്തൂ" : "നന്നായി!"}</div><div class="en">${s.motion.hint}</div>`);
  } else {
    vm.classList.add("hidden");
  }
  $("#verdict").style.display = "flex";
  setTimeout(() => ($("#verdict").style.display = "none"), 3500);
}

// ── coach rendering (routes through say()) ──────────────────────────────
function renderCoach(m) {
  const one = (r) => `<div class="mlbig">${r.say_ml || ""}</div><div class="en">${r.say_en || ""}</div>${r.say_manglish ? `<div class="en" style="color:#777;font-style:italic">${r.say_manglish}</div>` : ""}${r.drill_phrase != null ? `<div style="color:#777;font-size:12px;margin-top:6px">drill: phrase ${(+r.drill_phrase) + 1} @ ${Math.round(r.drill_bpm || 0)} bpm</div>` : ""}`;
  const head = (r) => `<h4><b>${r.engine || ""}</b> <span class="pill-badge ${r.on_device ? "dev" : "lap"}">${r.on_device ? "on-device" : "laptop"}</span> <span class="pill-badge">${r.model || ""}</span> <span class="pill-badge">${r.seconds != null ? r.seconds + " s" : ""}</span></h4>`;
  if (m.results && m.results.length > 1) {
    say(`<div class="side">${m.results.map((r) => `<div>${head(r)}${one(r)}</div>`).join("")}</div>`, { ms: 12000 });
  } else {
    say(`${m.engine ? head(m) : ""}${one(m)}`, { ms: 9000 });
  }
}

// ── WebSocket connect + dispatch ─────────────────────────────────────
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.type === "strike") {
      $("#hint").style.display = "none"; flashFoot(m.finger);
      if (m.judge === "auto") { markNote(m.note, "auto"); }
      else if (m.judge) {
        const map = { perfect: ["PERFECT · കൃത്യം", "#34c759"], good: ["GOOD · നല്ലത്", "#ffd60a"], late: ["LATE · വൈകി", "#ff9500"], early: ["EARLY · നേരത്തെ", "#ff9500"], wrong_finger: ["WRONG FINGER · തെറ്റായ വിരൽ", "#ff3b30"], extra: ["—", "#666"] };
        judge(...map[m.judge]);
        $("#pts").textContent = m.points; $("#streak").textContent = m.streak;
        if (m.note != null) markNote(m.note, m.judge);
      }
      triggerStrikeFx(m.finger, m.src);
    } else if (m.type === "click") {
      $("#hint").style.display = "none";
      const c = document.createElement("div");
      c.className = "click"; c.style.left = (m.finger * 20) + "%";
      c.style.background = m.down ? "rgba(255,214,10,.35)" : "rgba(255,255,255,.08)";
      $("#track").appendChild(c); setTimeout(() => c.remove(), 120);
      if (m.down) triggerStrikeFx(m.finger, "click");
    } else if (m.type === "score") {
      setScore(m.score);
      const conf = m.confidence != null ? ` · confidence ${Math.round(m.confidence * 100)}%` : "";
      $("#scoreInfo").innerHTML = `${m.score.title} · ${m.score.thaalam} · ${m.score.notes.length} notes · ${Math.round(m.score.bpm)} bpm${conf}<br><span class="mlbig" style="font-size:14px">${m.summary_ml || ""}</span><br><span class="en">${m.gemma || ""}</span>`;
      $("#status").textContent = `${m.score.thaalam}${conf}`;
      setActiveSec("practice");
    } else if (m.type === "practice_start") {
      startPractice(m.score, m.lead_in_s, !!m.listen);
    } else if (m.type === "miss") {
      m.notes.forEach((i) => markNote(i, "miss"));
      $("#streak").textContent = 0; judge("MISS · വിട്ടുപോയി", "#ff3b30");
    } else if (m.type === "practice_end") {
      play = null; showVerdict(m.summary);
      if (!ladder) setMode("idle");
    } else if (m.type === "coach") {
      renderCoach(m);
    } else if (m.type === "status") {
      $("#status").textContent = m.text;
    } else if (m.type === "kit") {
      $("#status").textContent = "kit: " + m.kit;
    } else if (m.type === "ladder_start") {
      onLadderStart(m);
    } else if (m.type === "ladder_step_up") {
      onLadderEvent(m, "step_up");
    } else if (m.type === "ladder_retry") {
      onLadderEvent(m, "retry");
    } else if (m.type === "ladder_complete") {
      onLadderEvent(m, "complete");
    }
  };
  ws.onclose = () => setTimeout(connect, 800);
}

// ── panel sections (rail + panel) ───────────────────────────────────────
function setActiveSec(sec) {
  document.querySelectorAll(".rail-btn").forEach((b) => b.classList.toggle("on", b.dataset.sec === sec));
  document.querySelectorAll(".panel-sec").forEach((el) => el.classList.toggle("hidden", el.dataset.sec !== sec));
}
document.querySelectorAll(".rail-btn").forEach((b) => (b.onclick = () => setActiveSec(b.dataset.sec)));
$("#panelToggle").onclick = () => $("#app").classList.toggle("collapsed");

// ── REST helpers ─────────────────────────────────────────────────────
async function loadState() {
  const s = await (await fetch("/api/state")).json();
  state = s;
  for (const id of ["kit", "ckit"]) {
    $("#" + id).innerHTML = Object.entries(s.kits).map(([k, v]) => `<option value="${k}" ${k === s.kit ? "selected" : ""}>${v.name}</option>`).join("");
  }
  if (s.score) setScore(s.score);
  $("#rig").textContent = s.dry ? "dry · laptop" : "glove live";
  $("#rig").classList.toggle("down", !!s.dry);
}
async function loadEngines() {
  try {
    const g = await (await fetch("/api/gemma")).json();
    const modes = [...g.engines.map((e) => e.engine)];
    if (g.engines.length > 1) modes.push("both");
    $("#engines").innerHTML = modes.map((mo) => {
      const e = g.engines.find((x) => x.engine === mo);
      const on = g.mode === mo;
      const badges = e
        ? `<span class="pill-badge ${e.on_device ? "dev" : "lap"}">${e.on_device ? "on-device" : "laptop"}</span><span class="pill-badge ${e.ok ? "" : "down"}">${e.model}${e.ok ? (e.loaded && e.loaded.includes(e.model) ? " · loaded" : "") : " · unreachable"}</span>`
        : `<span class="pill-badge">side by side</span>`;
      return `<div class="eng ${on ? "on" : ""}" data-mode="${mo}"><b>${mo === "both" ? "Both" : mo}</b>${badges}</div>`;
    }).join("");
    document.querySelectorAll(".eng").forEach((el) => (el.onclick = async () => {
      await fetch("/api/gemma/select", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ mode: el.dataset.mode }) });
      loadEngines();
    }));
    $("#engineNote").textContent = g.mode === "both" ? "Coaching runs on every engine in parallel — compare answers and speed." : `Learn, coach, game and compose use "${g.mode}".`;
  } catch (e) {
    $("#engineNote").textContent = "engine status unavailable";
  }
}
async function uploadLearn() {
  const f = $("#file").files[0];
  if (!f) return;
  const fd = new FormData(); fd.append("file", f);
  $("#status").textContent = "uploading…";
  const r = await fetch("/api/learn", { method: "POST", body: fd });
  const j = await r.json();
  $("#status").textContent = j.ok ? `learned ${j.notes} notes · ${j.thaalam}` : "error: " + j.error;
}
async function postCompose() {
  $("#status").textContent = "Gemini composing…";
  const r = await fetch("/api/compose", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ brief: $("#brief").value, kit: $("#ckit").value, cycles: 4, bpm: +$("#bpm").value }) });
  const j = await r.json();
  $("#status").textContent = j.ok ? `composed ${j.notes} notes` : "error: " + j.error;
}

// ── control wiring ───────────────────────────────────────────────────
$("#bpm").oninput = (e) => ($("#bpmv").textContent = e.target.value);
$("#kit").onchange = (e) => ws.send(JSON.stringify({ type: "kit", kit: e.target.value }));
$("#goFree").onclick = () => ws.send(JSON.stringify({ type: "free", bpm: +$("#bpm").value, cycle: +$("#cycle").value, click: $("#click").value }));
$("#stop").onclick = $("#stop2").onclick = () => { ws.send(JSON.stringify({ type: "stop" })); play = null; ladder = null; clearHudChip("ladder"); setMode("idle"); };
$("#upload").onclick = uploadLearn;
$("#compose").onclick = postCompose;
$("#loadPhrase").onclick = () => ws.send(JSON.stringify({ type: "phrase", text: $("#phraseText").value, bpm: +$("#bpm").value, cycles: 2 }));
$("#goListen").onclick = () => ws.send(JSON.stringify({ type: "listen", phrase: $("#phrase").value === "" ? null : +$("#phrase").value, speed: +$("#speed").value }));
$("#goPractice").onclick = () => ws.send(JSON.stringify({ type: "practice", phrase: $("#phrase").value === "" ? null : +$("#phrase").value, speed: +$("#speed").value }));
$("#goLadder").onclick = () => ws.send(JSON.stringify({ type: "ladder", phrase: $("#phrase").value === "" ? null : +$("#phrase").value, scales: DEFAULT_SCALES }));

// ── three.js stage ───────────────────────────────────────────────────
const MODEL_URL = "/assets/models/chenda/Chenda.glb";
let renderer = null, scene, camera, controls, drumGroup, zoneMeshes = [], labelEls = [], raycaster, has3D = false;
let zoneRadius = 0.05, modelScale = 1, laneH = 1;   // all re-derived from the real model in onModelLoaded
let noteMeshes = [], noteGeo = null, trailGeo = null, trailTex = null;
const ripples = []; // {mesh, t0}
let shakeVel = 0, shakeAmt = 0;

// Synthesia-style falling notes: each note rides down its finger's lane and lands on that
// finger's circle exactly on the beat. Same clock as the DOM notes (notesEl[i].dataset.t),
// so timing/judging is untouched — this is purely how it's drawn.
const LANE_H_MUL = 2.6;   // lane height, as a multiple of the head radius
const LANE_LOOK  = 0.22;  // how far up the lanes the camera looks. 0 puts the drum dead
                          // centre (highest in frame); bigger shows more runway above it.

function fadeLoading(msg) {
  const el = $("#loading");
  if (msg) el.querySelector("span:last-child").textContent = msg;
  el.classList.add("fade");
  setTimeout(() => el.classList.add("hidden"), 350);
}

function enterFallback(reason) {
  console.warn("3D stage unavailable, falling back to classic UI:", reason);
  $("#gl").classList.add("hidden");
  $("#zones").classList.add("hidden");
  $("#stage").classList.remove("has3d");        // flat overlay (hit line + notes) comes back
  document.querySelectorAll(".label3d").forEach((n) => n.remove());
  fadeLoading("3D stage unavailable — playing in classic mode.");
  has3D = false;
  // #track / #foot / keyboard / WS / ladder / motion / karaoke all keep working unmodified.
  requestAnimationFrame(classicLoop);
}
function classicLoop(now) {
  updateNotes(now);
  requestAnimationFrame(classicLoop);
}

function initStage() {
  let canvas = $("#gl");
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  } catch (err) {
    enterFallback(err); return;
  }
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b0b0b);
  camera = new THREE.PerspectiveCamera(45, 1, 0.01, 10000); // near/far re-tuned once the model's real scale is known
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const key = new THREE.DirectionalLight(0xffd98a, 1.1);
  key.position.set(2, 3, 2);
  scene.add(key);
  raycaster = new THREE.Raycaster();

  const resize = () => {
    const w = $("#stage").clientWidth, h = $("#stage").clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  };
  new ResizeObserver(resize).observe($("#stage"));
  resize();

  const timeout = setTimeout(() => enterFallback("model load timed out"), 8000);
  new GLTFLoader().load(
    MODEL_URL,
    (gltf) => { clearTimeout(timeout); onModelLoaded(gltf); },
    undefined,
    (err) => { clearTimeout(timeout); enterFallback(err); }
  );
}

function onModelLoaded(gltf) {
  has3D = true;
  drumGroup = new THREE.Group();
  drumGroup.add(gltf.scene);
  scene.add(drumGroup);

  const box = new THREE.Box3().setFromObject(gltf.scene);
  const size = box.getSize(new THREE.Vector3()), center = box.getCenter(new THREE.Vector3());
  const topY = box.max.y;
  const maxDim = Math.max(size.x, size.y, size.z) || 1;
  modelScale = maxDim;

  const head = new THREE.Vector3(center.x, topY, center.z);

  // Zones land where a hand actually falls on the head: a fanned arch reaching in from the
  // near side — middle finger deepest, thumb set wide and short, pinky short — rather than
  // five points spaced evenly around the rim, each one persistently colour-coded per finger.
  // Sit the zones ON the drumhead. box.max.y is the top of the whole model — which on this
  // chenda includes the ropes/straps rising above the head — so placing zones there left
  // them floating in mid-air. Raycast straight down at each zone's (x,z) and land on the
  // real surface underneath instead.
  scene.updateMatrixWorld(true);
  const down = new THREE.Raycaster(), DOWN = new THREE.Vector3(0, -1, 0);
  const surfaceY = (x, z) => {
    down.set(new THREE.Vector3(x, box.max.y + maxDim, z), DOWN);
    const hit = down.intersectObject(gltf.scene, true)[0];
    return hit ? hit.point.y : topY;
  };

  // The bounding box is WIDER than the playable skin — the ropes flare out past the head —
  // so sizing the hand off it pushed the outer zones over the rim. Probe outward from the
  // centre and keep the largest radius where the surface underneath is still the flat head
  // (same height as the centre), which excludes both the ropes and the falling-away barrel.
  const yHead = surfaceY(center.x, center.z), tol = maxDim * 0.02;
  const onHead = (r) => {
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 6) {
      if (Math.abs(surfaceY(center.x + Math.cos(a) * r, center.z + Math.sin(a) * r) - yHead) > tol) return false;
    }
    return true;
  };
  let headR = Math.max(size.x, size.z) / 2;
  for (let t = 0.95; t >= 0.2; t -= 0.05) {
    if (onHead(headR * t)) { headR *= t; break; }
  }

  const HAND = [
    [-58, 0.82],   // thumb  — set wide, sits shallower than the fingers
    [-28, 1.00],   // index
    [  0, 1.07],   // middle — reaches furthest
    [ 28, 1.01],   // ring
    [ 56, 0.86],   // pinky  — shortest
  ];
  const palmZ = center.z + headR * 0.95;   // heel of the hand, just inside the near rim
  const reach = headR * 0.95;
  zoneRadius = headR * 0.115;              // smaller pucks + wider fan = clearly separated lanes

  for (let i = 0; i < 5; i++) {
    const [deg, len] = HAND[i], a = THREE.MathUtils.degToRad(deg);
    const px = center.x + Math.sin(a) * len * reach;
    const pz = palmZ - Math.cos(a) * len * reach;
    const pos = new THREE.Vector3(px, surfaceY(px, pz) + maxDim * 0.0015, pz);

    const ringMat = new THREE.MeshBasicMaterial({ color: COLORS[i], transparent: true, opacity: 0.55, side: THREE.DoubleSide });
    const ring = new THREE.Mesh(new THREE.RingGeometry(zoneRadius * 1.05, zoneRadius * 1.2, 32), ringMat);
    ring.rotation.x = -Math.PI / 2; ring.position.copy(pos);
    drumGroup.add(ring);

    const geo = new THREE.CircleGeometry(zoneRadius, 32);
    const mat = new THREE.MeshBasicMaterial({ color: COLORS[i], transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const zone = new THREE.Mesh(geo, mat);
    zone.rotation.x = -Math.PI / 2; zone.position.copy(pos);
    zone.userData = { finger: i, name: NAMES[i], base: 0.3, hover: 0, anticipation: 0, flash: 0, ring };
    drumGroup.add(zone);
    zoneMeshes.push(zone);
  }

  // A faint column of light above each circle — the lane the notes ride down, so you can
  // read where a note is going before it arrives.
  laneH = headR * LANE_H_MUL;
  zoneMeshes.forEach((zone, i) => {
    const col = new THREE.Mesh(
      new THREE.CylinderGeometry(zoneRadius * 0.95, zoneRadius * 0.95, laneH, 20, 1, true),
      new THREE.MeshBasicMaterial({ color: COLORS[i], transparent: true, opacity: 0.06,
                                    side: THREE.DoubleSide, depthWrite: false }));
    col.position.set(zone.position.x, zone.position.y + laneH / 2, zone.position.z);
    drumGroup.add(col);
  });
  noteGeo = new THREE.CylinderGeometry(zoneRadius * 0.8, zoneRadius * 0.8, headR * 0.05, 24);

  // Comet trail behind each note. A canvas gradient (solid at the head, transparent at the
  // tail) painted on an open-ended cylinder — no custom shader needed, and one texture is
  // shared by every note. Additive blending makes it read as light rather than plastic.
  trailTex = makeTrailTexture();
  trailGeo = new THREE.PlaneGeometry(zoneRadius * 1.5, 1);
  trailGeo.translate(0, 0.5, 0);            // pivot at the bottom, so scale.y grows it upward

  // Frame the playfield now that the REAL head radius and lane height are known (doing this
  // off the raw bounding box sized the shot to the ropes, not the drum). Fit the taller of
  // the head and the lane runway, and look a little way up the lanes so notes are visible
  // on approach — LANE_LOOK is the knob: smaller lifts the drum higher in frame.
  const fitH = Math.max(headR * 2, laneH * 0.8);
  const dist = (fitH / 2) / Math.tan((camera.fov * Math.PI / 180) / 2) * 1.15;
  const elev = THREE.MathUtils.degToRad(34);   // tilted so the head reads as a disc and the lanes read as vertical
  const target = head.clone().setY(head.y + laneH * LANE_LOOK);
  camera.near = dist / 500;
  camera.far = dist * 50;
  camera.position.set(target.x, target.y + dist * Math.sin(elev), target.z + dist * Math.cos(elev));
  camera.updateProjectionMatrix();

  // Locked at a fixed angle: falling-note lanes only read correctly from a stable
  // viewpoint, so orbit and pan are off. Zoom stays, so the drum can still be sized to taste.
  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(target);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.enableRotate = false; controls.enablePan = false;
  controls.zoomSpeed = 0.7;
  controls.minDistance = dist * 0.45;
  controls.maxDistance = dist * 2.4;
  controls.update();

  // Labels live in #zones, not #track: #track is the flat 2D overlay (gold hit line,
  // falling notes, metronome flashes) and gets hidden entirely while the 3D stage drives
  // the visuals — the drum + its zones are the visualisation now.
  labelEls = zoneMeshes.map((zone) => {
    const el = document.createElement("div");
    el.className = "label3d"; el.style.display = "none";
    el.style.color = COLORS[zone.userData.finger];
    $("#zones").appendChild(el);
    return el;
  });
  $("#stage").classList.add("has3d");

  fadeLoading();

  renderer.domElement.style.pointerEvents = "auto";
  renderer.domElement.addEventListener("pointerdown", onPointerDown);
  renderer.domElement.addEventListener("pointerup", onPointerUp);
  renderer.domElement.addEventListener("pointermove", onPointerMove);
  renderer.domElement.addEventListener("pointerleave", () => setHover(-1));

  renderer.setAnimationLoop((time) => {
    controls.update();
    update3DNotes(time);          // #track (the flat DOM lane) is hidden in 3D — don't drive it
    updateZones(time);
    updateRipples(time);
    updateShake();
    updateLabels();
    renderer.render(scene, camera);
  });
}

function pointerNdc(ev) {
  const rect = renderer.domElement.getBoundingClientRect();
  return new THREE.Vector2(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
}
function zoneUnderPointer(ev) {
  raycaster.setFromCamera(pointerNdc(ev), camera);
  return raycaster.intersectObjects(zoneMeshes)[0];
}
// OrbitControls owns dragging, so a strike has to be a *tap*: short, and without travel.
// Otherwise every orbit gesture would also fire a note.
let downAt = null;
function onPointerDown(ev) { downAt = { x: ev.clientX, y: ev.clientY, t: performance.now() }; }
function onPointerUp(ev) {
  if (!downAt) return;
  const moved = Math.hypot(ev.clientX - downAt.x, ev.clientY - downAt.y);
  const held = performance.now() - downAt.t;
  downAt = null;
  if (moved > 6 || held > 500) return;          // that was an orbit drag, not a hit
  const hit = zoneUnderPointer(ev);
  if (hit) sendStrike(hit.object.userData.finger, 0.9, "zone3d");
}
let hoveredFinger = -1;
function onPointerMove(ev) {
  const hit = zoneUnderPointer(ev);
  setHover(hit ? hit.object.userData.finger : -1);
}
function setHover(finger) {
  if (finger === hoveredFinger) return;
  hoveredFinger = finger;
  zoneMeshes.forEach((z) => (z.userData.hover = z.userData.finger === finger ? 1 : 0));
}

// ── denote what's being played: anticipation glow for the next upcoming note per
// finger (mirrors the falling-note lane onto the drum itself), plus a bright flash
// exactly on a confirmed strike — both color-coded per finger, same COLORS as #foot/#track.
const ANTICIPATE_MS = 450;
function updateZones(now) {
  if (!zoneMeshes.length) return;
  const dtByFinger = nextNoteDtByFinger(now);
  zoneMeshes.forEach((zone) => {
    const u = zone.userData;
    const dt = dtByFinger[u.finger];
    u.anticipation = dt != null && dt >= -30 && dt < ANTICIPATE_MS ? 1 - Math.max(0, dt) / ANTICIPATE_MS : 0;
    u.flash *= 0.86; // fast decay after a strike
    const opacity = Math.min(0.95, u.base + u.hover * 0.15 + u.anticipation * 0.35 + u.flash * 0.55);
    const scale = 1 + u.anticipation * 0.08 + u.flash * 0.14 + Math.sin(now / 500 + u.finger) * 0.012;
    zone.material.opacity = opacity;
    zone.scale.set(scale, scale, scale);
    u.ring.material.opacity = Math.min(1, 0.55 + u.hover * 0.3 + u.flash * 0.45);
    u.ring.scale.set(scale, scale, scale);
  });
}
// ── Synthesia-style 3D falling notes ────────────────────────────────────
// A trail has to be a soft-edged billboard, not geometry you can see the sides of. Alpha
// falls off along the tail AND across the width, so there is no hard silhouette anywhere:
// squared falloff across gives a feathered edge rather than a visible rectangle.
function makeTrailTexture() {
  const W = 32, H = 128;
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const g = c.getContext("2d"), img = g.createImageData(W, H);
  for (let y = 0; y < H; y++) {
    const along = Math.pow(y / (H - 1), 1.8);          // row 0 = tail (three.js flips Y)
    for (let x = 0; x < W; x++) {
      const u = (x / (W - 1)) * 2 - 1;                 // -1..1 across the width
      const across = Math.max(0, 1 - u * u);
      const i = (y * W + x) * 4;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = 255;
      img.data[i + 3] = Math.round(along * across * across * 255);
    }
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.minFilter = THREE.LinearFilter;                     // no mip shimmer on a thin quad
  return t;
}
function clear3DNotes() {
  noteMeshes.forEach((g) => {
    if (!g) return;
    drumGroup.remove(g);
    g.children.forEach((c) => c.material.dispose());
  });
  noteMeshes = [];
}
function build3DNotes(s) {
  if (!has3D || !noteGeo) return;
  clear3DNotes();
  const trailLen = laneH * 0.16;
  noteMeshes = s.notes.map((n) => {
    const zone = zoneMeshes[n.finger];
    if (!zone) return null;
    const g = new THREE.Group();
    const puckMat = new THREE.MeshBasicMaterial({ color: COLORS[n.finger], transparent: true, opacity: 0.95 });
    g.add(new THREE.Mesh(noteGeo, puckMat));
    const trailMat = new THREE.MeshBasicMaterial({
      color: COLORS[n.finger], map: trailTex, transparent: true, opacity: 0.5,
      side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending });
    const trail = new THREE.Mesh(trailGeo, trailMat);
    trail.scale.y = trailLen;                 // sits on the puck, streaks back up the lane
    // Yaw the quad to face the camera. The camera is locked, and so is the lane, so this
    // is a one-time turn rather than per-frame billboarding.
    trail.rotation.y = Math.atan2(camera.position.x - zone.position.x, camera.position.z - zone.position.z);
    g.add(trail);
    g.position.copy(zone.position);
    g.visible = false;
    g.userData = { puckMat, trailMat, trail, trailLen };
    drumGroup.add(g);
    return g;
  });
}
function update3DNotes(now) {
  if (!noteMeshes.length || !play) return;
  for (let i = 0; i < noteMeshes.length; i++) {
    const m = noteMeshes[i], el = notesEl[i], n = score && score.notes[i];
    if (!m || !el || !n) continue;
    if (m.userData.consumed) { m.visible = false; continue; }
    const dt = +el.dataset.t - now;
    if (dt > APPROACH_MS || dt < -260) { m.visible = false; continue; }
    const zone = zoneMeshes[n.finger];
    const f = Math.max(0, dt) / APPROACH_MS;          // 1 at spawn, 0 exactly on the beat
    const u = m.userData;
    m.visible = true;
    m.position.set(zone.position.x, zone.position.y + f * laneH + zoneRadius * 0.2, zone.position.z);
    const fadeIn = Math.min(1, (1 - f) * 6);          // ease in at spawn instead of popping
    const fadeOut = dt < 0 ? Math.max(0, 1 + dt / 260) : 1;   // fade just past the beat
    u.puckMat.opacity = 0.95 * fadeIn * fadeOut;
    u.trailMat.opacity = 0.55 * fadeIn * fadeOut;
    u.trail.scale.y = u.trailLen * Math.min(1, f * 4);  // trail collapses into the pad on landing
  }
}

function nextNoteDtByFinger(now) {
  const out = [null, null, null, null, null];
  if (!play || !score) return out;
  notesEl.forEach((el, i) => {
    const n = score.notes[i];
    if (!n) return;
    const dt = +el.dataset.t - now;
    if (dt < -30) return; // already past the hit line
    if (out[n.finger] == null || dt < out[n.finger]) out[n.finger] = dt;
  });
  return out;
}

function triggerStrikeFx(finger, src) {
  if (!has3D) return;
  const zone = zoneMeshes[finger];
  if (zone) { spawnRipple(zone.position.clone()); zone.userData.flash = 1; }
  shakeVel += 0.06;
}
function spawnRipple(pos) {
  const geo = new THREE.RingGeometry(zoneRadius * 0.2, zoneRadius, 32);
  const mat = new THREE.MeshBasicMaterial({ color: 0xffd93d, transparent: true, opacity: 0.9, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.copy(pos).setY(pos.y + zoneRadius * 0.3);
  drumGroup.add(mesh);
  ripples.push({ mesh, t0: performance.now() });
}
function updateRipples(now) {
  for (let i = ripples.length - 1; i >= 0; i--) {
    const r = ripples[i], t = (now - r.t0) / 260;
    if (t >= 1) { drumGroup.remove(r.mesh); ripples.splice(i, 1); continue; }
    const scale = 1 + t * 1.8;                 // a soft ping at the zone, not a 8x shockwave
    r.mesh.scale.set(scale, scale, scale);
    r.mesh.material.opacity = 0.45 * (1 - t);
  }
}
function updateShake() {
  if (!drumGroup) return;
  shakeAmt += (shakeVel - shakeAmt) * 0.4;
  shakeVel *= 0.8;
  drumGroup.rotation.z = Math.sin(performance.now() / 40) * shakeAmt * 0.05;
  drumGroup.position.y = -shakeAmt * modelScale * 0.02;   // scale-relative, like the ripples
}
function updateLabels() {
  if (!labelEls.length) return;
  const stageEl = $("#stage"), w = stageEl.clientWidth, h = stageEl.clientHeight;
  zoneMeshes.forEach((zone, i) => {
    const el = labelEls[i], label = fmap.syllables[zone.userData.finger];
    const p = zone.position.clone().setY(zone.position.y + zoneRadius * 2.5).project(camera);
    if (!label || p.z > 1) { el.style.display = "none"; return; }
    el.style.display = "block";
    el.style.left = ((p.x * 0.5 + 0.5) * w) + "px";
    el.style.top = ((-p.y * 0.5 + 0.5) * h) + "px";
    el.textContent = label;
  });
}

// ── boot ──────────────────────────────────────────────────────────────
renderFoot();
connect();
loadState();
loadEngines();
setInterval(loadEngines, 15000);
initStage();
setTimeout(() => say(ASAN_IDLE, { ms: 7000 }), 1200);   // introduce Asan once the stage settles
