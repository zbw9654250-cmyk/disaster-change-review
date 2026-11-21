"use strict";

const byId = id => document.getElementById(id);
const buttons = byId("cases");

function showPhoto(id, photo) {
  const figure = byId(id);
  const image = figure.querySelector("img");
  image.src = "assets/" + photo.file;
  image.alt = photo.alt;
  figure.querySelector(".photo").href = image.getAttribute("src");
  const date = figure.querySelector("time");
  date.dateTime = photo.date;
  date.textContent = photo.date.replaceAll("-", ".");
  const marker = figure.querySelector(".marker");
  marker.hidden = !photo.box;
  if (photo.box) {
    const [x, y, width, height] = photo.box;
    Object.assign(marker.style, {
      left: x + "%", top: y + "%", width: width + "%", height: height + "%"
    });
  }
}

function selectCase(record) {
  byId("place").textContent = record.place;
  for (const field of ["evidence", "type", "severity", "basis"]) {
    byId(field).textContent = record[field];
  }
  showPhoto("before", record.before);
  showPhoto("after", record.after);
  document.querySelector(".comparison").classList.toggle("building", Boolean(record.before.box));
  const source = byId("source");
  source.textContent = record.credit;
  source.href = record.source;
  for (const button of buttons.children) {
    button.setAttribute("aria-pressed", String(button.value === record.id));
  }
}

for (const record of GALLERY) {
  const button = document.createElement("button");
  button.type = "button";
  button.value = record.id;
  button.textContent = record.name;
  button.addEventListener("click", () => selectCase(record));
  buttons.append(button);
}
selectCase(GALLERY[0]);
