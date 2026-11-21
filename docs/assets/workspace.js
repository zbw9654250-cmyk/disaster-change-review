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
  document.title = byId("heading").textContent;
}

const caseText = record => language === "en" ? record.en : record;

function viewLink(id, lang, phase) {
  const query = new URLSearchParams({lang, case: id});
  if (phase) query.set("phase", phase);
  return "?" + query;
}

function setLanguageLinks(record, phase) {
  for (const link of byId("languages").children) {
    const lang = link.lang === "en" ? "en" : "zh";
    link.href = viewLink(record.id, lang, phase) + (!phase && byId("baseline-comparison").open ? "#baseline-comparison" : "");
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
  const rings = GEO_CHANGES[record.id]?.rings ?? photo.rings ?? record.rings;
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
  setLanguageLinks(record);
  for (const button of buttons.children) {
    button.setAttribute("aria-pressed", String(button.value === record.id));
  }
}

const selected = GALLERY.find(record => record.id === params.get("case"));
const phase = params.get("phase");
if (selected && (phase === "before" || phase === "after")) {
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
  const benchmark = byId("baseline-comparison");
  benchmark.open = location.hash === "#baseline-comparison";
  benchmark.addEventListener("toggle", () => {
    const pressed = buttons.querySelector('[aria-pressed="true"]');
    if (pressed) setLanguageLinks(GALLERY.find(record => record.id === pressed.value));
  });
  for (const record of GALLERY) {
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
  selectCase(selected ?? GALLERY[0]);
}
