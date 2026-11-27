const files = document.querySelector("#files");
const drop = document.querySelector("#drop");
const selection = document.querySelector("#selection");
const mode = document.querySelector("#mode");
const details = document.querySelector("#details");
const preview = document.querySelector("#preview");
const submit = document.querySelector("#submit");
const status = document.querySelector("#status");
const jobs = document.querySelector("#jobs");
const count = document.querySelector("#count");
const descriptions = {
  four: "AI separation into vocals, drums, bass, and other instruments.",
  two: "AI separation into vocals and instrumental. Useful for karaoke or remixes.",
  quick: "Fast stereo center and sides extraction. Center includes any centered sound."
};
let chosen = [];
let uploading = false;
let lastJobs = "";
const rows = new Map();

function showFiles(next) {
  chosen = next;
  selection.replaceChildren();
  for (const file of chosen) {
    const item = document.createElement("li");
    item.textContent = file.name;
    selection.append(item);
  }
  submit.disabled = uploading || chosen.length === 0;
}

function download(label, url, name) {
  const link = document.createElement("a");
  link.textContent = label;
  link.href = url;
  link.download = name;
  return link;
}

function render(job) {
  const existing = rows.get(job.id);
  if (existing?.dataset.status === job.status) return existing;
  const row = document.createElement("article");
  row.className = "job";
  row.dataset.status = job.status;
  const heading = document.createElement("div");
  heading.className = "job-heading";
  const title = document.createElement("strong");
  title.textContent = job.name;
  const badge = document.createElement("span");
  badge.textContent = ({
    queued: "Queued", running: "Splitting…", done: "Ready", failed: "Failed", uploading: "Uploading…"
  })[job.status] + (job.preview ? " · 30s preview" : "");
  heading.append(title, badge);
  row.append(heading);
  if (job.error) {
    const error = document.createElement("p");
    error.textContent = job.error;
    row.append(error);
  }
  if (job.stems) {
    const base = "/files/" + job.id + "/";
    const name = job.name.replace(/\.[^.]+$/, "") + (job.preview ? "-preview" : "");
    for (const stem of job.stems) {
      const track = document.createElement("div");
      track.className = "stem";
      const label = document.createElement("span");
      label.textContent = stem.replace(".wav", "").replaceAll("_", " ");
      const audio = document.createElement("audio");
      audio.controls = true;
      audio.preload = "none";
      audio.src = base + stem;
      audio.setAttribute("aria-label", label.textContent);
      track.append(label, audio, download("WAV", base + stem, name + "-" + stem));
      row.append(track);
    }
    row.append(download("Download all stems (.zip)", base + "stems.zip", name + "-stems.zip"));
  }
  rows.set(job.id, row);
  return row;
}

async function refresh() {
  try {
    const response = await fetch("/api/jobs");
    if (!response.ok) return;
    const data = await response.text();
    if (data === lastJobs) return;
    lastJobs = data;
    const list = JSON.parse(data);
    count.textContent = list.length + (list.length === 1 ? " job" : " jobs");
    const present = new Set(list.map(job => job.id));
    for (const [id, row] of rows) {
      if (!present.has(id)) {
        row.remove();
        rows.delete(id);
      }
    }
    if (!list.length) return;
    jobs.querySelector(".empty")?.remove();
    list.forEach((job, index) => {
      const row = render(job);
      if (jobs.children[index] !== row) jobs.insertBefore(row, jobs.children[index] || null);
    });
    const current = new Set(rows.values());
    for (const row of [...jobs.children]) {
      if (!current.has(row)) row.remove();
    }
  } catch {
    // Polling resumes automatically when the local server responds.
  }
}

files.addEventListener("change", () => showFiles([...files.files]));
mode.addEventListener("change", () => { details.textContent = descriptions[mode.value]; });
details.textContent = descriptions[mode.value];
drop.addEventListener("dragover", event => {
  event.preventDefault();
  drop.classList.add("active");
});
drop.addEventListener("dragleave", () => drop.classList.remove("active"));
drop.addEventListener("drop", event => {
  event.preventDefault();
  drop.classList.remove("active");
  showFiles([...event.dataTransfer.files]);
});
submit.addEventListener("click", async () => {
  const batch = [...chosen];
  const settings = {mode: mode.value, preview: preview.checked ? "1" : "0"};
  uploading = true;
  files.disabled = true;
  showFiles([]);
  const failed = [];
  const messages = [];
  for (const file of batch) {
    status.textContent = "Queuing " + file.name + "…";
    try {
      if (!file.size || file.size > 250 * 1024 * 1024) throw new Error("Choose a file up to 250 MB.");
      const response = await fetch("/api/jobs", {
        method: "POST",
        headers: {
          "X-Blacktable": "upload", "X-File-Name": encodeURIComponent(file.name),
          "X-Split-Mode": settings.mode, "X-Preview": settings.preview
        },
        body: file
      });
      if (!response.ok) throw new Error((await response.json()).error || "Upload failed.");
    } catch (error) {
      failed.push(file);
      messages.push(file.name + " — " + error.message);
    }
  }
  files.value = "";
  files.disabled = false;
  uploading = false;
  showFiles([...failed, ...chosen]);
  status.textContent = messages.length ? messages.join(" ") : "";
});

async function poll() {
  await refresh();
  window.setTimeout(poll, 1200);
}
poll();
