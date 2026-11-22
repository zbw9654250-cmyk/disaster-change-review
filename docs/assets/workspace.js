"use strict";

const byId = id => document.getElementById(id);
const buttons = byId("cases");
const baselineButtons = [...document.querySelectorAll("#baseline-options button")];
const params = new URLSearchParams(location.search);
const preferenceKey = "disaster-change-review-language";
const requestedLanguage = params.get("lang");
let language = requestedLanguage === "en" ? "en" : "zh";
const baselineModels = ["rgb", "fc_siam_diff", "bit"];
const baselineLabels = {
  rgb: {zh: "RGB 规则基线", en: "RGB-rule-v1"},
  fc_siam_diff: {zh: "FC-Siam-Diff", en: "FC-Siam-Diff"},
  bit: {zh: "BIT", en: "BIT"},
};
let baselineModel = baselineModels.includes(params.get("baseline")) ? params.get("baseline") : "rgb";
const baselineOutputs = typeof BASELINE_OUTPUTS === "undefined" ? {} : BASELINE_OUTPUTS;
let activeRecord = null;
try {
  if (requestedLanguage === "en" || requestedLanguage === "zh") {
    localStorage.setItem(preferenceKey, language);
  } else if (localStorage.getItem(preferenceKey) === "en") {
    language = "en";
  }
} catch {
  // With storage blocked, the language in the URL still works for every link.
}
if (language === "en") {
  document.documentElement.lang = "en";
  for (const node of document.querySelectorAll("[data-en]")) {
    node.textContent = node.dataset.en;
  }
  for (const node of document.querySelectorAll("[data-en-label]")) {
    node.setAttribute("aria-label", node.dataset.enLabel);
  }
  byId("credits").href = "DATA-NOTICE.en.md";
  document.title = byId("heading").textContent;
}

const caseText = record => language === "en" ? record.en : record;
const featuredGallery = GALLERY.filter(record => record.featured !== false);

function viewLink(id, lang, phase, baseline = baselineModel) {
  const query = new URLSearchParams({lang, case: id});
  if (phase) query.set("phase", phase);
  if (baseline && baseline !== "rgb") query.set("baseline", baseline);
  return "?" + query;
}

function setLanguageLinks(record, phase) {
  for (const link of byId("languages").children) {
    const lang = link.lang === "en" ? "en" : "zh";
    link.href = viewLink(record.id, lang, phase, baselineModel);
    link.setAttribute("aria-current", String(lang === language));
  }
}

function baselineResult(record) {
  const regions = CHANGE_REGIONS[record.id] || {};
  if (baselineModel === "rgb") return baselineOutputs[record.id]?.rgb || regions.baseline;
  return baselineOutputs[record.id]?.[baselineModel] || null;
}

function updateBaselineControls(record) {
  const regions = CHANGE_REGIONS[record.id] || {};
  for (const button of baselineButtons) {
    const available = button.value === "rgb"
      ? Boolean(baselineOutputs[record.id]?.rgb || regions.baseline)
      : Boolean(baselineOutputs[record.id]?.[button.value]);
    button.disabled = !available;
    button.setAttribute("aria-pressed", String(button.value === baselineModel));
    button.title = available ? "" : (language === "en" ? "Run this model to enable it" : "运行该模型后可用");
    const status = button.querySelector("em");
    if (status) {
      status.textContent = button.value === baselineModel
        ? (language === "en" ? "shown here" : "当前展示")
        : available
          ? (language === "en" ? "available" : "可用")
          : (language === "en" ? "optional run" : "可选运行");
    }
  }
}

function updateBaselineDetails(record) {
  const node = byId("baseline-details");
  if (!node) return;
  const result = baselineResult(record);
  const metrics = result?.metrics;
  if (!metrics) {
    node.textContent = language === "en"
      ? "RGB-rule-v1 runs on CPU and returns the orange candidate rings."
      : "RGB-rule-v1 在 CPU 上运行，返回橙色候选圈。";
    return;
  }
  const contours = Number(metrics.contour_count || 0);
  const fraction = (Number(metrics.mask_fraction || 0) * 100).toFixed(2);
  const latency = Math.round(Number(metrics.latency_ms || 0));
  node.textContent = language === "en"
    ? `${baselineLabels[baselineModel].en}: ${contours} contours, ${fraction}% mask, ${latency} ms on ${metrics.device || "GPU"}. LEVIR-CD checkpoint, zero-shot cross-domain output.`
    : `${baselineLabels[baselineModel].zh}：${contours} 个轮廓，掩膜占比 ${fraction}%，${latency} ms，运行设备 ${metrics.device || "GPU"}。结果来自 LEVIR-CD checkpoint 的跨数据集零样本推理。`;
}

function chooseBaseline(model, record) {
  if (!baselineModels.includes(model)) return;
  if (model !== "rgb" && !baselineOutputs[record.id]?.[model]) return;
  baselineModel = model;
  try {
    history.replaceState(null, "", viewLink(record.id, language, null, baselineModel));
  } catch {
    location.assign(viewLink(record.id, language, null, baselineModel));
    return;
  }
  selectCase(record);
}

function showPhoto(phase, record) {
  const photo = phase === "before" ? record.before : record.after;
  const figure = byId(phase);
  const image = figure.querySelector("img");
  image.src = "assets/" + photo.file;
  image.alt = language === "en" ? record.en[(phase === "before" ? "before" : "after") + "Alt"] : photo.alt;
  figure.querySelector(".photo").href = viewLink(record.id, language, phase);
  const date = figure.querySelector("time");
  date.dateTime = photo.date;
  date.textContent = language === "en" ? photo.date : photo.date.replaceAll("-", ".");
  const regions = CHANGE_REGIONS[record.id];
  const selectedBaseline = phase === "baseline" ? baselineResult(record) : null;
  const contours = phase === "baseline" ? (selectedBaseline?.contours || [])
    : phase === "ours" ? (regions.ours.contours || []) : [];
  const rings = phase === "baseline" ? (selectedBaseline?.rings || [])
    : phase === "ours" && !contours.length ? regions.ours.rings : [];
  figure.classList.toggle("baseline-panel", phase === "baseline");
  figure.classList.toggle("ours-panel", phase === "ours");
  figure.querySelector(".rings").replaceChildren(...rings.map(([x, y, width, height, angle = 0]) => {
    const ring = document.createElement("span");
    ring.className = "ring " + (phase === "baseline" ? "baseline-ring" : "ours-ring");
    Object.assign(ring.style, {
      left: x + "%", top: y + "%", width: width + "%", height: height + "%",
      transform: "rotate(" + angle + "deg)"
    });
    return ring;
  }));
  const contourLayer = figure.querySelector(".contours");
  contourLayer.replaceChildren(...contours.map(points => {
    const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    polygon.setAttribute("points", points.map(([x, y]) => `${x},${y}`).join(" "));
    polygon.setAttribute("vector-effect", "non-scaling-stroke");
    polygon.setAttribute("aria-hidden", "true");
    return polygon;
  }));
  if (phase === "baseline") {
    const label = baselineLabels[baselineModel][language];
    figure.querySelector("figcaption strong").textContent = language === "en"
      ? "After · " + label : "灾后 · " + label;
  }
}

function selectCase(record) {
  if (baselineModel !== "rgb" && !baselineOutputs[record.id]?.[baselineModel]) {
    baselineModel = "rgb";
  }
  activeRecord = record;
  const text = caseText(record);
  for (const field of ["place", "evidence", "type", "severity", "basis"]) {
    byId(field).textContent = text[field];
  }
  updateBaselineControls(record);
  updateBaselineDetails(record);
  showPhoto("before", record);
  showPhoto("baseline", record);
  showPhoto("ours", record);
  const source = byId("source");
  source.textContent = text.credit;
  source.href = record.source;
  setLanguageLinks(record);
  for (const button of buttons.children) {
    button.setAttribute("aria-pressed", String(button.value === record.id));
  }
}

for (const button of baselineButtons) {
  button.addEventListener("click", () => {
    const record = activeRecord || featuredGallery[0];
    chooseBaseline(button.value, record);
  });
}

const selected = GALLERY.find(record => record.id === params.get("case"));
if (selected && baselineModel !== "rgb" && !baselineOutputs[selected.id]?.[baselineModel]) {
  baselineModel = "rgb";
}
const phase = params.get("phase");
if (selected && ["before", "baseline", "ours"].includes(phase)) {
  setLanguageLinks(selected, phase);
  showPhoto(phase, selected);
  const figure = byId(phase);
  figure.querySelector("figcaption").append(byId("languages"));
  // The enlarged view uses the same image-relative annotations as the comparison.
  const link = figure.querySelector(".photo");
  const photo = document.createElement("div");
  photo.className = "photo";
  photo.append(...link.childNodes);
  link.replaceWith(photo);
  figure.classList.add("enlarged");
  document.querySelector("main").replaceChildren(figure);
  document.title = caseText(selected).name + " · " + figure.querySelector("strong").textContent;
} else {
  for (const record of featuredGallery) {
    const button = document.createElement("button");
    button.type = "button";
    button.value = record.id;
    button.textContent = caseText(record).name;
    button.addEventListener("click", () => {
      const link = viewLink(record.id, language);
      try {
        history.replaceState(null, "", link);
      } catch {
        // Some browsers restrict History API calls on local files.
        location.assign(link);
        return;
      }
      selectCase(record);
    });
    buttons.append(button);
  }
  selectCase(selected ?? featuredGallery[0]);
}

