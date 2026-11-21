"use strict";

const byId = id => document.getElementById(id);
const buttons = byId("cases");
const params = new URLSearchParams(location.search);
const preferenceKey = "disaster-change-review-language";
const requestedLanguage = params.get("lang");
let language = requestedLanguage === "en" ? "en" : "zh";
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
  byId("review-credits").href = "DATA-NOTICE.en.md";
}

const caseText = record => language === "en" ? record.en : record;

function viewLink(id, lang, phase) {
  const query = new URLSearchParams({lang, case: id});
  if (phase) query.set("phase", phase);
  return "?" + query;
}

function setLanguageLinks(makeLink) {
  for (const link of byId("languages").children) {
    const lang = link.lang === "en" ? "en" : "zh";
    link.href = makeLink(lang);
    link.setAttribute("aria-current", String(lang === language));
  }
}

function showPhoto(phase, record) {
  const photo = record[phase];
  const figure = byId(phase);
  const image = figure.querySelector("img");
  image.src = "assets/" + photo.file;
  image.alt = language === "en" ? record.en[phase + "Alt"] : photo.alt;
  figure.querySelector(".photo").href = viewLink(record.id, language, phase);
  const date = figure.querySelector("time");
  date.dateTime = photo.date;
  date.textContent = language === "en" ? photo.date : photo.date.replaceAll("-", ".");
  const rings = photo.rings ?? record.rings;
  figure.querySelector(".rings").replaceChildren(...rings.map(([x, y, width, height, angle = 0]) => {
    const ring = document.createElement("span");
    ring.className = "ring";
    Object.assign(ring.style, {
      left: x + "%", top: y + "%", width: width + "%", height: height + "%",
      transform: "rotate(" + angle + "deg)"
    });
    return ring;
  }));
}

function selectCase(record) {
  const text = caseText(record);
  for (const field of ["place", "evidence", "type", "severity", "basis"]) {
    byId(field).textContent = text[field];
  }
  showPhoto("before", record);
  showPhoto("after", record);
  const source = byId("source");
  source.textContent = text.credit;
  source.href = record.source;
  setLanguageLinks(lang => viewLink(record.id, lang));
  for (const button of buttons.children) {
    button.setAttribute("aria-pressed", String(button.value === record.id));
  }
}

function replaceUrl(href) {
  try {
    history.replaceState(null, "", href);
    return true;
  } catch {
    // A local file can still navigate when the browser restricts the History API.
    location.assign(href);
    return false;
  }
}

function renderOutlines(svg, record, method) {
  svg.setAttribute("viewBox", "0 0 " + record.width + " " + record.height);
  svg.replaceChildren();
  for (const [lines, style] of [[record[method], "prediction"], [record.reference, "reference"]]) {
    for (const d of lines) {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("class", style);
      path.setAttribute("d", d);
      svg.append(path);
    }
  }
}

function startReview() {
  const toggle = byId("reference-toggle");
  const dialog = byId("image-dialog");
  let selected = REVIEW_CASES.find(item => item.id === params.get("sample")) ?? REVIEW_CASES[0];
  toggle.checked = params.get("ref") !== "0";

  function sampleLink(lang) {
    const query = new URLSearchParams({lang, sample: selected.id});
    if (!toggle.checked) query.set("ref", "0");
    return "?" + query;
  }

  function syncReference() {
    document.body.classList.toggle("hide-reference", !toggle.checked);
    setLanguageLinks(sampleLink);
  }

  function showSample() {
    const copy = selected[language];
    byId("sample-title").textContent = "Ebenezer · " + (language === "en" ? "Feature " : "标注 ") + selected.fid;
    byId("sample-evidence").textContent = copy.evidence;
    for (const method of ["baseline", "current"]) {
      const figure = byId(method);
      const image = figure.querySelector("img");
      image.src = selected.image;
      image.alt = copy.alt;
      const button = figure.querySelector("button");
      const methodName = figure.querySelector("strong").textContent;
      button.setAttribute("aria-label", language === "en" ? "Enlarge " + methodName.toLowerCase() + " outlines" : "放大" + methodName + "轮廓");
      figure.querySelector(".score").textContent = (language === "en" ? "Best IoU " : "最佳 IoU ") + selected[method + "Iou"].toFixed(3);
      renderOutlines(figure.querySelector("svg"), selected, method);
    }
    for (const button of byId("review-cases").children) {
      button.setAttribute("aria-pressed", String(button.value === selected.id));
    }
    syncReference();
  }

  if (REVIEW_CASES.length > 1) {
    for (const item of REVIEW_CASES) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = item[language].name;
      button.value = item.id;
      button.addEventListener("click", () => {
        selected = item;
        if (replaceUrl(sampleLink(language))) showSample();
      });
      byId("review-cases").append(button);
    }
  } else {
    byId("review-cases").hidden = true;
  }
  toggle.addEventListener("change", () => {
    if (replaceUrl(sampleLink(language))) syncReference();
  });
  for (const button of document.querySelectorAll(".model-photo")) {
    button.addEventListener("click", () => {
      const figure = button.closest("figure");
      byId("zoom-title").textContent = selected[language].name + " · " + figure.querySelector("strong").textContent;
      byId("zoom-photo").replaceChildren(...[...button.children].map(el => el.cloneNode(true)));
      dialog.showModal();
    });
  }
  byId("close-zoom").addEventListener("click", () => dialog.close());
  showSample();
}

const selected = GALLERY.find(record => record.id === params.get("case"));
const phase = params.get("phase");
const isGallery = Boolean(selected) || params.get("view") === "gallery";
byId("review-link").href = "?" + new URLSearchParams({lang: language});
byId("gallery-link").href = "?" + new URLSearchParams({lang: language, view: "gallery"});
byId(isGallery ? "gallery-link" : "review-link").setAttribute("aria-current", "page");
byId(isGallery ? "event-gallery" : "model-review").hidden = false;
byId(isGallery ? "model-review" : "event-gallery").remove();
if (isGallery) byId("image-dialog").remove();
document.title = byId(isGallery ? "heading" : "review-title").textContent;
if (!isGallery) {
  startReview();
} else if (selected && (phase === "before" || phase === "after")) {
  setLanguageLinks(lang => viewLink(selected.id, lang, phase));
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
  for (const record of GALLERY) {
    const button = document.createElement("button");
    button.type = "button";
    button.value = record.id;
    button.textContent = caseText(record).name;
    button.addEventListener("click", () => {
      const link = viewLink(record.id, language);
      if (replaceUrl(link)) selectCase(record);
    });
    buttons.append(button);
  }
  selectCase(selected ?? GALLERY[0]);
}
