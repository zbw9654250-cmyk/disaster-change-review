"use strict";

const byId = id => document.getElementById(id);
const asset = name => "assets/" + name;
const selectedDefault = "b-a9482fc5ef0d";
const ordered = [ROOFS.find(record => record.id === selectedDefault), ...ROOFS.filter(record => record.id !== selectedDefault)];
const state = { record: ordered[0], layout: "pair", view: "scene" };
const map = byId("map");
const panes = { pre: byId("left-pane"), post: byId("right-pane") };

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function pressedSet(selector, key, val) {
  document.querySelectorAll(selector).forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset[key] === val));
  });
}

function mountStages() {
  for (const pane of Object.values(panes)) {
    const stage = element("div", undefined, "map-stage");
    stage.append(...Array.from(pane.children));
    pane.append(stage);
  }
}

function sizeStages() {
  for (const pane of Object.values(panes)) {
    pane.style.setProperty("--pane-width", pane.clientWidth + "px");
  }
}

function listCases() {
  const value = byId("event-filter").value;
  const visible = ordered.filter(record => !value || record.event === value);
  const entries = visible.map(record => {
    const button = element("button", undefined, "case-item");
    button.type = "button";
    button.dataset.id = record.id;
    button.setAttribute("aria-pressed", String(record.id === state.record.id));
    const thumbnail = element("img");
    thumbnail.alt = "";
    thumbnail.src = asset(record.phase.post.scene);
    const caption = element("span");
    caption.append(element("strong", record.event), element("small", record.id));
    button.append(thumbnail, caption);
    if (record.id === state.record.id) {
      const arrow = element("span", "›", "arr");
      arrow.setAttribute("aria-hidden", "true");
      button.append(arrow);
    }
    button.addEventListener("click", () => changeCase(record, true));
    return button;
  });
  byId("case-list").replaceChildren(...entries);
  byId("case-count").textContent = visible.length;
}

function showMap() {
  const detail = state.view === "detail";
  const wipe = state.layout === "wipe";
  const record = state.record;
  map.classList.toggle("detail", detail);
  map.classList.toggle("wipe", wipe);
  byId("wipe-controls").hidden = !wipe;
  byId("wipe-handle").hidden = !wipe;
  for (const [phase, pane] of Object.entries(panes)) {
    const data = record.phase[phase];
    const image = pane.querySelector(".scene");
    const outline = pane.querySelector(".outline");
    const roi = pane.querySelector(".roi");
    image.src = asset(detail ? data.detail : data.scene);
    image.alt = record.event + " " + record.id + (phase === "pre" ? " 灾前" : " 灾后") + (detail ? "测量选区放大图" : "场景裁图");
    outline.src = asset(data.outline);
    outline.hidden = detail || !byId("show-mask").checked;
    roi.hidden = detail || !byId("show-roi").checked;
    const [left, top, right, bottom] = data.roi;
    Object.assign(roi.style, { left: 100 * left + "%", top: 100 * top + "%",
      width: 100 * (right - left) + "%", height: 100 * (bottom - top) + "%" });
  }
  byId("show-mask").disabled = detail;
  byId("show-roi").disabled = detail;
  pressedSet("[data-layout]", "layout", state.layout);
  pressedSet("[data-view]", "view", state.view);
  sizeStages();
}

function changeCase(record, refocus = false) {
  state.record = record;
  byId("case-name").textContent = record.event;
  byId("place").textContent = record.place + "  /  " + record.id;
  byId("explanation").textContent = record.explain;
  byId("region").textContent = "足迹" + record.region + "选区";
  byId("mode").textContent = record.mode === "visual_fact_selection" ? "Qwen3-VL · 已选择本栋测量事实" : "Qwen3-VL 未选择有效项，采用测量说明";
  for (const phase of ["pre", "post"]) byId(phase + "-luma").textContent = record.phase[phase].luma.toFixed(1);
  const methods = [["原视觉 RAG", record.old], ["当前建筑的图像测量", record.measure], ["图像测量 + Qwen3-VL 核验", record.explain]];
  byId("methods").replaceChildren(...methods.map(([title, text]) => {
    const entry = element("div", undefined, "entry");
    entry.append(element("h3", title), element("p", text));
    return entry;
  }));
  const dl = element("dl");
  const fields = [
    ["原始图块", record.tile], ["建筑 UID", record.uid],
    ["xBD 整栋标注", record.label + "（项目映射为" + record.grade + "）"],
    ["灾前证据框", record.phase.pre.window.join(", ")], ["灾后证据框", record.phase.post.window.join(", ")],
    ["坐标单位", "336 × 336 建筑裁图上的像素，按左、上、右、下排列。"],
    ["共同有效格", record.valid + " / 2304"], ["像素比较", record.state + "（选区可见外观）"]
  ];
  for (const [key, val] of fields) dl.append(element("dt", key), element("dd", val));
  byId("provenance").replaceChildren(dl);
  listCases();
  showMap();
  if (refocus) byId("case-list").querySelector('[aria-pressed="true"]').focus({ preventScroll: true });
}

function displayTab() {
  const hash = location.hash.substring(1);
  const name = ["review", "bench", "sources"].includes(hash) ? hash : "review";
  for (const id of ["review", "bench", "sources"]) {
    byId(id).hidden = id !== name;
    const link = byId("tab-" + id);
    if (id === name) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (hash !== "main") window.scrollTo(0, 0);
  sizeStages();
}

mountStages();
new ResizeObserver(sizeStages).observe(map);
for (const eventName of new Set(ordered.map(record => record.event))) {
  byId("event-filter").add(new Option(eventName, eventName));
}
byId("event-filter").addEventListener("change", event => {
  const value = event.target.value;
  if (value && state.record.event !== value) changeCase(ordered.find(record => record.event === value));
  else listCases();
});
document.querySelectorAll("[data-layout]").forEach(button => button.addEventListener("click", () => {
  state.layout = button.dataset.layout;
  showMap();
}));
document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => {
  state.view = button.dataset.view;
  showMap();
}));
byId("show-mask").addEventListener("change", showMap);
byId("show-roi").addEventListener("change", showMap);
function setWipe(value) {
  const amount = Math.max(0, Math.min(100, Math.round(value)));
  byId("wipe-range").value = amount;
  const ratio = amount + "%";
  map.style.setProperty("--wipe", ratio);
  byId("wipe-percent").textContent = ratio;
}
byId("wipe-range").addEventListener("input", event => setWipe(Number(event.target.value)));
function moveWipe(event) {
  const bounds = map.getBoundingClientRect();
  setWipe(100 * (event.clientX - bounds.left) / bounds.width);
}
map.addEventListener("pointerdown", event => {
  if (state.layout !== "wipe" || event.button !== 0 || !event.isPrimary) return;
  map.setPointerCapture(event.pointerId);
  moveWipe(event);
});
map.addEventListener("pointermove", event => {
  if (map.hasPointerCapture(event.pointerId)) moveWipe(event);
});
window.addEventListener("hashchange", displayTab);
changeCase(state.record);
displayTab();
