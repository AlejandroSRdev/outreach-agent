const API_URL = import.meta.env.VITE_API_URL;

const LEADS = [
  { id: 1,  name: "Alice Johnson",    company: "Acme Corp",         role: "VP of Engineering" },
  { id: 2,  name: "Bob Martinez",     company: "TechStream",        role: "CTO" },
  { id: 3,  name: "Carol White",      company: "DataBridge",        role: "Head of Product" },
  { id: 4,  name: "David Kim",        company: "NovaSystems",       role: "Engineering Manager" },
  { id: 5,  name: "Emma Davis",       company: "CloudPeak",         role: "Director of Operations" },
  { id: 6,  name: "Frank Nguyen",     company: "InfraTech",         role: "Platform Lead" },
  { id: 7,  name: "Grace Lee",        company: "Finlytics",         role: "COO" },
  { id: 8,  name: "Henry Brown",      company: "Stackwell",         role: "VP of Sales" },
  { id: 9,  name: "Irene Torres",     company: "Loopify",           role: "Chief Product Officer" },
  { id: 10, name: "James Wilson",     company: "Orbiton",           role: "Head of Growth" },
  { id: 11, name: "Karen Hall",       company: "Pivotal Labs",      role: "Software Architect" },
  { id: 12, name: "Liam Scott",       company: "Meridian AI",       role: "ML Engineering Lead" },
  { id: 13, name: "Maria Gonzalez",   company: "Syntho",            role: "Director of Engineering" },
  { id: 14, name: "Nathan Clark",     company: "ByteForge",         role: "CEO" },
  { id: 15, name: "Olivia Adams",     company: "Fluxbase",          role: "Product Manager" },
  { id: 16, name: "Paul Wright",      company: "Zephyr Networks",   role: "Infrastructure Lead" },
  { id: 17, name: "Quinn Murphy",     company: "Cortexia",          role: "VP of Product" },
  { id: 18, name: "Rachel Baker",     company: "Launchpad Inc",     role: "Head of Engineering" },
  { id: 19, name: "Samuel Carter",    company: "Gridline",          role: "CTO" },
  { id: 20, name: "Tina Robinson",    company: "Wavelength Co",     role: "Director of Technology" },
];

const leadById = {};
LEADS.forEach(function (l) { leadById[l.id] = l; });

function getDisplayName(apiLead) {
  // On success, the API returns enriched.name (human-readable string).
  // On failure, the API returns str(lead.lead_id) (numeric string) — look up locally.
  const asInt = parseInt(apiLead, 10);
  if (!isNaN(asInt) && leadById[asInt]) {
    return leadById[asInt].name;
  }
  return apiLead;
}

let selectedLeads = [];
let isLoading = false;

function renderTable() {
  const container = document.getElementById("lead-table-container");

  const table = document.createElement("table");

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  ["Name", "Company", "Role", "Select"].forEach(function (text) {
    const th = document.createElement("th");
    th.textContent = text;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  LEADS.forEach(function (lead, index) {
    const tr = document.createElement("tr");

    const tdName = document.createElement("td");
    tdName.textContent = lead.name;
    tr.appendChild(tdName);

    const tdCompany = document.createElement("td");
    tdCompany.textContent = lead.company;
    tr.appendChild(tdCompany);

    const tdRole = document.createElement("td");
    tdRole.textContent = lead.role;
    tr.appendChild(tdRole);

    const tdSelect = document.createElement("td");
    tdSelect.className = "col-select";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.index = index;
    checkbox.addEventListener("change", function () {
      onCheckboxChange(checkbox, lead);
    });
    tdSelect.appendChild(checkbox);
    tr.appendChild(tdSelect);

    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

function onCheckboxChange(checkbox, lead) {
  if (checkbox.checked) {
    // Cap at 20 — revert if already at limit
    if (selectedLeads.length >= 20) {
      checkbox.checked = false;
      return;
    }
    selectedLeads.push(lead);
  } else {
    selectedLeads = selectedLeads.filter(function (l) {
      return l.id !== lead.id;
    });
  }

  updateSelectionUI();
}

function updateSelectionUI() {
  document.getElementById("selection-counter").textContent =
    "Selected: " + selectedLeads.length + " / 20";

  const runBtn = document.getElementById("run-btn");
  runBtn.disabled = selectedLeads.length === 0;
}

async function runBatch() {
  isLoading = true;

  const runBtn = document.getElementById("run-btn");
  const statusMsg = document.getElementById("status-msg");
  const resultsContainer = document.getElementById("results-container");

  runBtn.disabled = true;
  statusMsg.textContent = "Processing batch...";
  resultsContainer.innerHTML = "";

  try {
    console.log("[runBatch] API_URL:", API_URL, "| endpoint:", `${API_URL}/outreach/batch`);

    const response = await fetch(`${API_URL}/outreach/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ leads: selectedLeads.map(function (l) { return { lead_id: l.id }; }) }),
    });

    console.log("[runBatch] fetch resolved — status:", response.status, "| ok:", response.ok, "| type:", response.type, "| url:", response.url);

    if (response.ok) {
      let data;
      try {
        data = await response.json();
      } catch (jsonErr) {
        const rawText = await response.clone().text();
        console.error("[runBatch] JSON parse failed:");
        console.error("  name:", jsonErr.name);
        console.error("  message:", jsonErr.message);
        console.error("  stack:", jsonErr.stack);
        console.error("  raw response text:", rawText);
        renderError("Response parse error — invalid JSON from server");
        return;
      }
      renderResults(data.results);
    } else {
      renderError("Server error: " + response.status);
    }
  } catch (err) {
    console.error("[runBatch] catch block hit — full error:", err);
    console.error("  name:", err.name);
    console.error("  message:", err.message);
    console.error("  stack:", err.stack);
    renderError("Network error — backend unreachable");
  } finally {
    isLoading = false;
    runBtn.disabled = false;
    statusMsg.textContent = "";
  }
}

function renderResults(data) {
  const container = document.getElementById("results-container");

  data.forEach(function (item) {
    const block = document.createElement("div");
    block.className = "result-block";

    const header = document.createElement("div");
    header.className = "result-header";
    header.textContent = getDisplayName(item.lead);
    block.appendChild(header);

    const statusLine = document.createElement("div");
    if (item.status === "success") {
      statusLine.className = "status-success";
      statusLine.textContent = "Status: success";
    } else {
      statusLine.className = "status-failed";
      statusLine.textContent = "Status: failed";
    }
    block.appendChild(statusLine);

    if (item.status === "success" && item.result) {
      const subjectLine = document.createElement("div");
      subjectLine.className = "result-subject";
      subjectLine.textContent = "Subject: " + item.result.subject;
      block.appendChild(subjectLine);

      const textarea = document.createElement("textarea");
      textarea.readOnly = true;
      textarea.value = item.result.body;
      block.appendChild(textarea);

      const copyBtn = document.createElement("button");
      copyBtn.className = "copy-btn";
      copyBtn.textContent = "Copy";
      copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(textarea.value).then(function () {
          copyBtn.textContent = "Copied!";
          setTimeout(function () {
            copyBtn.textContent = "Copy";
          }, 1500);
        });
      });
      block.appendChild(copyBtn);
    } else {
      // Failed or missing result — render error message safely
      const errorLine = document.createElement("div");
      errorLine.className = "result-error";
      errorLine.textContent = "Error: " + (item.error || "Unknown error");
      block.appendChild(errorLine);
    }

    container.appendChild(block);
  });
}

function renderError(message) {
  const container = document.getElementById("results-container");

  const block = document.createElement("div");
  block.className = "result-error-global";

  const strong = document.createElement("strong");
  strong.textContent = "Error:";
  block.appendChild(strong);

  block.appendChild(document.createTextNode(" " + message));
  container.appendChild(block);
}

// Init
document.getElementById("run-btn").addEventListener("click", runBatch);
renderTable();
