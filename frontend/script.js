const subjectInput = document.getElementById("subjectInput");
const bodyInput = document.getElementById("bodyInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const errorHint = document.getElementById("errorHint");
const scanOverlay = document.getElementById("scanOverlay");
const brandMark = document.getElementById("brandMark");

const emptyState = document.getElementById("emptyState");
const resultContent = document.getElementById("resultContent");
const statusSub = document.getElementById("statusSub");

const verdictBadge = document.getElementById("verdictBadge");
const verdictLabel = document.getElementById("verdictLabel");
const confidenceValue = document.getElementById("confidenceValue");
const confidenceFill = document.getElementById("confidenceFill");
const probBars = document.getElementById("probBars");
const triggerList = document.getElementById("triggerList");
const noTriggerNote = document.getElementById("noTriggerNote");
const highlightedText = document.getElementById("highlightedText");

const modelAccuracy = document.getElementById("modelAccuracy");
const footerStats = document.getElementById("footerStats");

const SAMPLES = {
  lottery: {
    subject: "CONGRATULATIONS! You've WON $850,000!!!",
    body: "Dear Winner, we are pleased to inform you that your email address has won $850,000 in the International Online Lottery. To claim your prize, click here: http://claim-reward-now.biz/4471 and provide your full name, address and bank details within 24 hours or your prize will be forfeited. Act now, this offer will not be repeated!!!"
  },
  phishing: {
    subject: "Your account has been LIMITED",
    body: "We detected unusual activity on your account. For your safety we have temporarily limited access. Click here to verify your identity immediately: http://secure-verify-account.info/2291 You must act within 24 hours or your account will be permanently closed."
  },
  promo: {
    subject: "Flash sale: 30% off ends tonight",
    body: "Hi there, our biggest sale of the season ends at midnight. Shop your favorites before they're gone. As always, unsubscribe anytime from the link in our footer."
  },
  work: {
    subject: "Meeting notes from today's sync",
    body: "Hi team, thanks for joining the call today. I've attached the notes from our discussion about the project timeline. Let me know if I missed anything and we can go over it again tomorrow morning."
  },
  personal: {
    subject: "Dinner this weekend?",
    body: "Hey, are you free for dinner this Saturday? Thinking of trying that new place downtown we talked about. Let me know what time works for you!"
  }
};

document.querySelectorAll(".sample-chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    const sample = SAMPLES[btn.dataset.sample];
    subjectInput.value = sample.subject;
    bodyInput.value = sample.body;
    errorHint.textContent = "";
  });
});

clearBtn.addEventListener("click", () => {
  subjectInput.value = "";
  bodyInput.value = "";
  errorHint.textContent = "";
  resultContent.hidden = true;
  emptyState.hidden = false;
  statusSub.textContent = "waiting for input";
});

analyzeBtn.addEventListener("click", analyze);
bodyInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) analyze();
});

async function analyze() {
  const subject = subjectInput.value.trim();
  const body = bodyInput.value.trim();
  const combined = [subject, body].filter(Boolean).join(". ");

  if (!combined) {
    errorHint.textContent = "Type or paste an email first — the box can't be empty.";
    return;
  }
  errorHint.textContent = "";

  setScanning(true);

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: combined })
    });
    const data = await res.json();

    if (!res.ok) {
      errorHint.textContent = data.error || "Something went wrong analyzing this message.";
      setScanning(false);
      return;
    }

    renderResult(data, body || subject);
  } catch (err) {
    errorHint.textContent = "Couldn't reach the server. Is the Flask app running?";
  } finally {
    setScanning(false);
  }
}

function setScanning(isScanning) {
  analyzeBtn.disabled = isScanning;
  analyzeBtn.querySelector(".btn-label").textContent = isScanning ? "Scanning…" : "Analyze message";
  brandMark.classList.toggle("scanning", isScanning);
  if (isScanning) {
    scanOverlay.classList.remove("active");
    void scanOverlay.offsetWidth; // restart animation
    scanOverlay.classList.add("active");
    statusSub.textContent = "scanning message…";
  }
}

function renderResult(data, rawText) {
  emptyState.hidden = true;
  resultContent.hidden = false;
  statusSub.textContent = `analyzed with ${data.model_used.replace("_", " ")}`;

  const isSpam = data.label === "spam";

  verdictBadge.className = "verdict-badge " + (isSpam ? "spam" : "ham");
  verdictLabel.textContent = isSpam ? "⚠ Likely spam" : "✓ Looks legitimate";

  confidenceValue.textContent = `${data.confidence}%`;
  confidenceFill.className = "confidence-fill " + (isSpam ? "spam" : "ham");
  requestAnimationFrame(() => { confidenceFill.style.width = `${data.confidence}%`; });

  probBars.innerHTML = "";
  const order = ["spam", "ham"];
  order.forEach((cls) => {
    const val = data.probabilities[cls] ?? 0;
    const row = document.createElement("div");
    row.className = "prob-row";
    row.innerHTML = `
      <span class="label">${cls}</span>
      <span class="track"><span class="fill" style="width:${val}%; background:${cls === "spam" ? "var(--amber)" : "var(--green)"}"></span></span>
      <span class="val">${val}%</span>
    `;
    probBars.appendChild(row);
  });

  triggerList.innerHTML = "";
  if (data.trigger_words && data.trigger_words.length > 0) {
    noTriggerNote.hidden = true;
    data.trigger_words.forEach((word) => {
      const tag = document.createElement("span");
      tag.className = "trigger-tag";
      tag.textContent = word;
      triggerList.appendChild(tag);
    });
  } else {
    noTriggerNote.hidden = false;
  }

  highlightedText.innerHTML = highlightWords(rawText, data.trigger_words || []);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function highlightWords(text, words) {
  let safe = escapeHtml(text);
  const sorted = [...words].sort((a, b) => b.length - a.length);
  sorted.forEach((word) => {
    const escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(`(${escapedWord})`, "gi");
    safe = safe.replace(re, "<mark>$1</mark>");
  });
  return safe;
}

async function loadMetrics() {
  try {
    const res = await fetch("/api/metrics");
    const data = await res.json();
    const best = data.results[data.best_model];
    modelAccuracy.textContent = `${(best.accuracy * 100).toFixed(1)}%`;
    footerStats.textContent =
      `Model: ${data.best_model.replace("_", " ")} · trained on ${data.n_train} messages, ` +
      `tested on ${data.n_test} · accuracy ${(best.accuracy * 100).toFixed(1)}% · ` +
      `precision ${(best.precision * 100).toFixed(1)}% · recall ${(best.recall * 100).toFixed(1)}%`;
  } catch (err) {
    footerStats.textContent = "Couldn't load model stats.";
  }
}

loadMetrics();
