"use strict";

const byId = id => document.getElementById(id);
const buttons = byId("cases");

function showPhoto(phase, record) {
  const photo = record[phase];
  const figure = byId(phase);
  const image = figure.querySelector("img");
  image.src = "assets/" + photo.file;
  image.alt = photo.alt;
  figure.querySelector(".photo").href = "?" + new URLSearchParams({case: record.id, phase});
  const date = figure.querySelector("time");
  date.dateTime = photo.date;
  date.textContent = photo.date.replaceAll("-", ".");
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
  byId("place").textContent = record.place;
  for (const field of ["evidence", "type", "severity", "basis"]) {
    byId(field).textContent = record[field];
  }
  showPhoto("before", record);
  showPhoto("after", record);
  document.querySelector(".comparison").classList.toggle("building", record.subject === "building");
  const source = byId("source");
  source.textContent = record.credit;
  source.href = record.source;
  for (const button of buttons.children) {
    button.setAttribute("aria-pressed", String(button.value === record.id));
  }
}

const params = new URLSearchParams(location.search);
const selected = GALLERY.find(record => record.id === params.get("case"));
const phase = params.get("phase");
if (selected && (phase === "before" || phase === "after")) {
  showPhoto(phase, selected);
  const figure = byId(phase);
  // The enlarged view uses the same image-relative annotations as the comparison.
  const link = figure.querySelector(".photo");
  const photo = document.createElement("div");
  photo.className = "photo";
  photo.append(...link.childNodes);
  link.replaceWith(photo);
  figure.classList.add("enlarged");
  document.querySelector("main").replaceChildren(figure);
  document.title = selected.name + " · " + figure.querySelector("strong").textContent;
} else {
  for (const record of GALLERY) {
    const button = document.createElement("button");
    button.type = "button";
    button.value = record.id;
    button.textContent = record.name;
    button.addEventListener("click", () => selectCase(record));
    buttons.append(button);
  }
  selectCase(GALLERY[0]);
}
