/* app.js - frontend logic: talks to the Flask API and draws tables/charts */

// ---------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------
const COLORS = ["#2563eb", "#16a34a", "#d97706", "#9333ea", "#dc2626",
                "#0891b2", "#be185d", "#65a30d", "#4f46e5", "#ea580c"];

let editingPid = null;      // PID being edited (null = adding a new process)
let pidColors = {};         // PID -> color, so a process keeps the same color everywhere

// Shortcut for document.getElementById
function $(id) { return document.getElementById(id); }

// Make text safe to put inside HTML
function esc(text) {
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

// Call the backend API and return the JSON (throws an Error on failure)
async function api(url, method = "GET", body = null) {
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (body !== null) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  let data = {};
  try {
    data = await response.json();
  } catch (e) {
    // the server did not send JSON (for example a crash); handled below
  }
  if (!response.ok) throw new Error(data.error || "Server error (" + response.status + ")");
  return data;
}

// Show a green (success) or red (error) message at the top
let messageTimer = null;
function showMessage(text, type = "success") {
  const box = $("message");
  box.textContent = text;
  box.className = "message " + type;
  clearTimeout(messageTimer);
  messageTimer = setTimeout(() => box.classList.add("hidden"), 4000);
}

// Run an async action and show any error in the message bar
async function safely(action) {
  try {
    await action();
  } catch (error) {
    showMessage(error.message, "error");
  }
}

function colorFor(pid) {
  if (pid === "IDLE") return null;
  if (!(pid in pidColors)) {
    pidColors[pid] = COLORS[Object.keys(pidColors).length % COLORS.length];
  }
  return pidColors[pid];
}

// ---------------------------------------------------------------
// 1. PROCESSES
// ---------------------------------------------------------------
async function loadProcesses() {
  const processes = await api("/api/processes");
  const body = $("processTable");

  if (processes.length === 0) {
    body.innerHTML = '<tr class="empty"><td colspan="5">No processes yet. Add one or load sample data.</td></tr>';
    return;
  }

  body.innerHTML = "";
  for (const p of processes) {
    colorFor(p.pid);
    const row = document.createElement("tr");
    row.innerHTML =
      "<td>" + esc(p.pid) + "</td><td>" + p.arrival + "</td><td>" + p.burst +
      "</td><td>" + p.priority + "</td>" +
      '<td><button class="small secondary" data-edit="' + esc(p.pid) + '">Edit</button>' +
      '<button class="small danger" data-delete="' + esc(p.pid) + '">Delete</button></td>';
    body.appendChild(row);
  }
}

// Reset the form back to "add" mode
function resetForm() {
  editingPid = null;
  $("processForm").reset();
  $("arrival").value = 0;
  $("burst").value = 1;
  $("priority").value = 1;
  $("pid").disabled = false;
  $("submitBtn").textContent = "Add Process";
  $("cancelEditBtn").classList.add("hidden");
}

// Add a new process or save changes to an existing one
$("processForm").addEventListener("submit", (event) => {
  event.preventDefault();
  safely(async () => {
    const data = {
      pid: $("pid").value.trim(),
      arrival: $("arrival").value,
      burst: $("burst").value,
      priority: $("priority").value,
    };
    if (editingPid === null) {
      await api("/api/processes", "POST", data);
      showMessage("Process " + data.pid + " added");
    } else {
      await api("/api/processes/" + encodeURIComponent(editingPid), "PUT", data);
      showMessage("Process " + editingPid + " updated");
    }
    resetForm();
    await loadProcesses();
  });
});

$("cancelEditBtn").addEventListener("click", resetForm);

// Edit / Delete buttons inside the table (event delegation)
$("processTable").addEventListener("click", (event) => {
  const editPid = event.target.getAttribute("data-edit");
  const deletePid = event.target.getAttribute("data-delete");

  if (editPid) {
    safely(async () => {
      const processes = await api("/api/processes");
      const p = processes.find((item) => item.pid === editPid);
      if (!p) return;
      editingPid = p.pid;
      $("pid").value = p.pid;
      $("pid").disabled = true;              // PID cannot be changed
      $("arrival").value = p.arrival;
      $("burst").value = p.burst;
      $("priority").value = p.priority;
      $("submitBtn").textContent = "Save Changes";
      $("cancelEditBtn").classList.remove("hidden");
      $("pid").scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  if (deletePid) {
    safely(async () => {
      await api("/api/processes/" + encodeURIComponent(deletePid), "DELETE");
      if (editingPid === deletePid) resetForm();
      showMessage("Process " + deletePid + " deleted");
      await loadProcesses();
    });
  }
});

$("sampleBtn").addEventListener("click", () => {
  safely(async () => {
    await api("/api/processes/sample", "POST");
    resetForm();
    showMessage("Sample data loaded");
    await loadProcesses();
  });
});

$("clearBtn").addEventListener("click", () => {
  if (!confirm("Delete all processes?")) return;
  safely(async () => {
    await api("/api/processes", "DELETE");
    resetForm();
    showMessage("All processes deleted");
    await loadProcesses();
  });
});

// ---------------------------------------------------------------
// 2. GANTT CHART DRAWING
// ---------------------------------------------------------------
// Fill two elements: one with colored blocks, one with the time numbers under them
function drawGantt(blocksEl, timesEl, gantt) {
  blocksEl.innerHTML = "";
  timesEl.innerHTML = "";
  if (gantt.length === 0) return;

  const total = gantt[gantt.length - 1].end;
  const unit = Math.max(18, Math.min(40, Math.floor(900 / total)));   // pixels per time unit

  for (const g of gantt) {
    const width = (g.end - g.start) * unit;

    const block = document.createElement("div");
    block.className = "gantt-block" + (g.pid === "IDLE" ? " idle" : "");
    block.style.width = width + "px";
    if (g.pid !== "IDLE") block.style.background = colorFor(g.pid);
    block.textContent = g.pid;
    block.title = g.pid + ": " + g.start + " to " + g.end;
    blocksEl.appendChild(block);

    const tick = document.createElement("div");
    tick.className = "gantt-tick";
    tick.style.width = width + "px";
    tick.textContent = g.start;
    timesEl.appendChild(tick);
  }

  const endTick = document.createElement("div");
  endTick.className = "gantt-tick end";
  endTick.textContent = total;
  timesEl.appendChild(endTick);
}

// ---------------------------------------------------------------
// 3. RUN ONE ALGORITHM
// ---------------------------------------------------------------
$("algorithm").addEventListener("change", () => {
  $("quantumLabel").classList.toggle("hidden", $("algorithm").value !== "RR");
});

// Show one result: Gantt chart, metrics table and averages
function showResult(result, quantum) {
  let title = "Result: " + result.algorithm;
  if (result.algorithm === "RR" && quantum) title += " (quantum = " + quantum + ")";
  $("resultTitle").textContent = title;

  drawGantt($("gantt"), $("ganttTimes"), result.gantt);

  const body = $("resultTable");
  body.innerHTML = "";
  for (const p of result.processes) {
    const row = document.createElement("tr");
    row.innerHTML =
      "<td>" + esc(p.pid) + "</td><td>" + p.arrival + "</td><td>" + p.burst +
      "</td><td>" + p.priority + "</td><td>" + p.completion +
      "</td><td>" + p.turnaround + "</td><td>" + p.waiting + "</td>";
    body.appendChild(row);
  }

  $("avgWaiting").textContent = result.avg_waiting;
  $("avgTurnaround").textContent = result.avg_turnaround;
  $("resultCard").classList.remove("hidden");
}

$("runBtn").addEventListener("click", () => {
  safely(async () => {
    const algorithm = $("algorithm").value;
    const quantum = $("quantum").value;
    const result = await api("/api/simulate", "POST", { algorithm: algorithm, quantum: quantum });
    showResult(result, quantum);
    $("resultCard").scrollIntoView({ behavior: "smooth" });
    showMessage(result.algorithm + " finished (saved as run #" + result.run_id + ")");
    await loadHistory();
  });
});

// ---------------------------------------------------------------
// 4. COMPARE ALL ALGORITHMS
// ---------------------------------------------------------------
$("compareBtn").addEventListener("click", () => {
  safely(async () => {
    const quantum = $("quantum").value || 2;
    const data = await api("/api/compare", "POST", { quantum: quantum });
    showComparison(data, quantum);
    $("compareCard").scrollIntoView({ behavior: "smooth" });
    showMessage("Comparison done. Best average waiting time: " + data.best_algorithm);
    await loadHistory();
  });
});

function showComparison(data, quantum) {
  $("bestText").textContent =
    "Best (lowest average waiting time): " + data.best_algorithm + "  |  Round Robin quantum = " + quantum;

  // Table + bar chart
  const tableBody = $("compareTable");
  const bars = $("compareBars");
  tableBody.innerHTML = "";
  bars.innerHTML = "";

  let maxWaiting = 0;
  for (const s of data.summary) maxWaiting = Math.max(maxWaiting, s.avg_waiting);

  for (const s of data.summary) {
    const isBest = s.algorithm === data.best_algorithm;

    const row = document.createElement("tr");
    if (isBest) row.className = "best-row";
    row.innerHTML = "<td>" + s.algorithm + "</td><td>" + s.avg_waiting +
                    "</td><td>" + s.avg_turnaround + "</td>";
    tableBody.appendChild(row);

    const percent = maxWaiting > 0 ? (s.avg_waiting / maxWaiting) * 100 : 0;
    const barRow = document.createElement("div");
    barRow.className = "bar-row";
    barRow.innerHTML =
      '<div class="bar-label">' + s.algorithm + "</div>" +
      '<div class="bar-track"><div class="bar-fill' + (isBest ? " best" : "") +
      '" style="width:' + percent + '%"></div></div>' +
      '<div class="bar-value">' + s.avg_waiting + "</div>";
    bars.appendChild(barRow);
  }

  // One Gantt chart per algorithm
  const holder = $("compareGantts");
  holder.innerHTML = "";
  for (const result of data.results) {
    const title = document.createElement("div");
    title.className = "compare-gantt-title";
    title.textContent = result.algorithm;

    const scroll = document.createElement("div");
    scroll.className = "gantt-scroll";
    const blocks = document.createElement("div");
    blocks.className = "gantt";
    const times = document.createElement("div");
    times.className = "gantt-times";
    scroll.appendChild(blocks);
    scroll.appendChild(times);

    holder.appendChild(title);
    holder.appendChild(scroll);
    drawGantt(blocks, times, result.gantt);
  }

  $("compareCard").classList.remove("hidden");
}

// ---------------------------------------------------------------
// 5. HISTORY (from the database)
// ---------------------------------------------------------------
async function loadHistory() {
  const runs = await api("/api/runs");
  const body = $("historyTable");

  if (runs.length === 0) {
    body.innerHTML = '<tr class="empty"><td colspan="7">No runs saved yet.</td></tr>';
    return;
  }

  body.innerHTML = "";
  for (const r of runs) {
    const row = document.createElement("tr");
    row.innerHTML =
      "<td>" + r.id + "</td><td>" + esc(r.algorithm) + "</td><td>" +
      (r.quantum === null ? "-" : r.quantum) + "</td><td>" + r.avg_waiting +
      "</td><td>" + r.avg_turnaround + "</td><td>" + esc(r.created_at) + "</td>" +
      '<td><button class="small" data-run="' + r.id + '">View</button></td>';
    body.appendChild(row);
  }
}

$("historyTable").addEventListener("click", (event) => {
  const runId = event.target.getAttribute("data-run");
  if (!runId) return;
  safely(async () => {
    const run = await api("/api/runs/" + runId);
    showResult(run.result, run.quantum);
    $("resultCard").scrollIntoView({ behavior: "smooth" });
  });
});

$("clearHistoryBtn").addEventListener("click", () => {
  if (!confirm("Delete the whole run history?")) return;
  safely(async () => {
    await api("/api/runs", "DELETE");
    showMessage("History cleared");
    await loadHistory();
  });
});

// ---------------------------------------------------------------
// Start: load saved data from the database when the page opens
// ---------------------------------------------------------------
safely(async () => {
  await loadProcesses();
  await loadHistory();
});
