/**
 * open-avatar-cast 前端：选角色 → TTS → 音量驱动口型
 * 适合作为 OBS「浏览器源」捕获。
 */

(() => {
  "use strict";

  const els = {
    select: document.getElementById("character-select"),
    text: document.getElementById("text-input"),
    useLlm: document.getElementById("use-llm"),
    btnSpeak: document.getElementById("btn-speak"),
    btnStop: document.getElementById("btn-stop"),
    obsMode: document.getElementById("obs-mode"),
    avatarStage: document.getElementById("avatar-stage"),
    status: document.getElementById("status"),
    meta: document.getElementById("meta"),
  };

  /** @type {Record<string, any>} */
  let charactersById = {};
  /** @type {string} */
  let currentId = "";
  /** @type {HTMLAudioElement | null} */
  let audioEl = null;
  /** @type {AudioContext | null} */
  let audioCtx = null;
  /** @type {AnalyserNode | null} */
  let analyser = null;
  /** @type {MediaElementAudioSourceNode | null} */
  let sourceNode = null;
  /** @type {number | null} */
  let rafId = null;
  let mouthBaseRy = 6;
  let lipCfg = { min_scale: 0.15, max_scale: 1.0, smoothing: 0.35 };
  let smoothLevel = 0;

  function setStatus(msg) {
    els.status.textContent = msg;
  }

  function setMeta(text) {
    els.meta.textContent = text;
  }

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${url} → ${res.status}`);
    return res.json();
  }

  async function loadCharacters() {
    const data = await fetchJSON("/api/characters");
    charactersById = {};
    els.select.innerHTML = "";
    for (const c of data.characters) {
      charactersById[c.id] = c;
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `${c.name} (${c.id})`;
      els.select.appendChild(opt);
    }
    currentId = data.default && charactersById[data.default]
      ? data.default
      : (data.characters[0] && data.characters[0].id) || "";
    if (currentId) {
      els.select.value = currentId;
      await loadAvatar(currentId);
    }
    setMeta(`角色 ${data.characters.length} 个 · 默认 ${data.default || "-"}`);
  }

  async function loadAvatar(id) {
    const c = charactersById[id];
    if (!c) return;
    currentId = id;
    lipCfg = Object.assign(
      { min_scale: 0.15, max_scale: 1.0, smoothing: 0.35 },
      c.lip_sync || {}
    );
    const res = await fetch(c.avatar_url);
    if (!res.ok) throw new Error("头像加载失败");
    const svgText = await res.text();
    els.avatarStage.innerHTML = svgText;
    const mouth = els.avatarStage.querySelector("#mouth");
    if (mouth) {
      const ry = mouth.getAttribute("ry");
      mouthBaseRy = ry ? parseFloat(ry) : 6;
    }
    setStatus(`${c.name} 已加载`);
  }

  function getMouth() {
    return els.avatarStage.querySelector("#mouth");
  }

  function setMouthOpen(scale) {
    const mouth = getMouth();
    if (!mouth) return;
    const s = Math.max(lipCfg.min_scale, Math.min(lipCfg.max_scale, scale));
    mouth.setAttribute("ry", String(mouthBaseRy * (0.4 + s * 1.6)));
    // 略微加宽，更像开口
    const rx0 = parseFloat(mouth.getAttribute("data-rx0") || mouth.getAttribute("rx") || "18");
    if (!mouth.getAttribute("data-rx0")) mouth.setAttribute("data-rx0", String(rx0));
    mouth.setAttribute("rx", String(rx0 * (0.85 + s * 0.35)));
  }

  function ensureAudioGraph(audio) {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    // 每个新 audio 元素重建连接
    if (sourceNode) {
      try { sourceNode.disconnect(); } catch (_) {}
      sourceNode = null;
    }
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.5;
    sourceNode = audioCtx.createMediaElementSource(audio);
    sourceNode.connect(analyser);
    analyser.connect(audioCtx.destination);
  }

  function stopLipLoop() {
    if (rafId != null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    smoothLevel = 0;
    setMouthOpen(lipCfg.min_scale);
  }

  function startLipLoop() {
    stopLipLoop();
    const data = new Uint8Array(analyser ? analyser.frequencyBinCount : 0);

    function tick() {
      if (!analyser) return;
      analyser.getByteFrequencyData(data);
      // 取中低频能量作为「口型开合」近似
      let sum = 0;
      const n = Math.min(32, data.length);
      for (let i = 0; i < n; i++) sum += data[i];
      const level = n ? sum / (n * 255) : 0;
      const a = lipCfg.smoothing;
      smoothLevel = smoothLevel * (1 - a) + level * a;
      setMouthOpen(smoothLevel * 1.8);
      rafId = requestAnimationFrame(tick);
    }
    rafId = requestAnimationFrame(tick);
  }

  function stopPlayback() {
    stopLipLoop();
    if (audioEl) {
      audioEl.pause();
      audioEl.src = "";
      audioEl = null;
    }
    setStatus("已停止");
    els.btnSpeak.disabled = false;
  }

  async function speak() {
    const text = (els.text.value || "").trim();
    if (!text) {
      setStatus("请输入文本");
      return;
    }
    stopPlayback();
    els.btnSpeak.disabled = true;
    setStatus("合成中…");

    try {
      const res = await fetch("/api/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          character_id: currentId || null,
          use_llm: !!els.useLlm.checked,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.crossOrigin = "anonymous";
      audioEl = audio;

      ensureAudioGraph(audio);
      audio.onplay = () => {
        setStatus("播报中…");
        startLipLoop();
      };
      audio.onended = () => {
        stopLipLoop();
        URL.revokeObjectURL(url);
        setStatus("播报完成");
        els.btnSpeak.disabled = false;
        setMeta(
          `voice=${res.headers.get("X-OAC-Voice") || "-"} · ` +
          `provider=${res.headers.get("X-OAC-Provider") || "-"} · ` +
          `llm=${res.headers.get("X-OAC-LLM-Used") || "0"}`
        );
      };
      audio.onerror = () => {
        stopLipLoop();
        setStatus("播放失败");
        els.btnSpeak.disabled = false;
      };
      await audio.play();
    } catch (err) {
      console.error(err);
      setStatus(`错误: ${err.message || err}`);
      els.btnSpeak.disabled = false;
    }
  }

  // URL 参数：?obs=1 自动隐藏面板；?text= 预填
  function applyQuery() {
    const q = new URLSearchParams(location.search);
    if (q.get("obs") === "1" || q.get("obs") === "true") {
      els.obsMode.checked = true;
      document.body.classList.add("obs-mode");
    }
    const t = q.get("text");
    if (t) els.text.value = t;
    const ch = q.get("character");
    if (ch) {
      // 等角色加载后再切
      window.__pendingCharacter = ch;
    }
  }

  els.select.addEventListener("change", () => loadAvatar(els.select.value));
  els.btnSpeak.addEventListener("click", speak);
  els.btnStop.addEventListener("click", stopPlayback);
  els.obsMode.addEventListener("change", () => {
    document.body.classList.toggle("obs-mode", els.obsMode.checked);
  });
  els.text.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      speak();
    }
  });

  applyQuery();
  loadCharacters()
    .then(() => {
      const pending = window.__pendingCharacter;
      if (pending && charactersById[pending]) {
        els.select.value = pending;
        return loadAvatar(pending);
      }
    })
    .catch((err) => {
      console.error(err);
      setStatus(`初始化失败: ${err.message || err}`);
    });
})();
