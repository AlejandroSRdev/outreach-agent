const API_URL = import.meta.env.VITE_API_URL;

const LEADS = [
  { name: "Alice Johnson",    company: "Acme Corp",         role: "VP of Engineering" },
  { name: "Bob Martinez",     company: "TechStream",        role: "CTO" },
  { name: "Carol White",      company: "DataBridge",        role: "Head of Product" },
  { name: "David Kim",        company: "NovaSystems",       role: "Engineering Manager" },
  { name: "Emma Davis",       company: "CloudPeak",         role: "Director of Operations" },
  { name: "Frank Nguyen",     company: "InfraTech",         role: "Platform Lead" },
  { name: "Grace Lee",        company: "Finlytics",         role: "COO" },
  { name: "Henry Brown",      company: "Stackwell",         role: "VP of Sales" },
  { name: "Irene Torres",     company: "Loopify",           role: "Chief Product Officer" },
  { name: "James Wilson",     company: "Orbiton",           role: "Head of Growth" },
  { name: "Karen Hall",       company: "Pivotal Labs",      role: "Software Architect" },
  { name: "Liam Scott",       company: "Meridian AI",       role: "ML Engineering Lead" },
  { name: "Maria Gonzalez",   company: "Syntho",            role: "Director of Engineering" },
  { name: "Nathan Clark",     company: "ByteForge",         role: "CEO" },
  { name: "Olivia Adams",     company: "Fluxbase",          role: "Product Manager" },
  { name: "Paul Wright",      company: "Zephyr Networks",   role: "Infrastructure Lead" },
  { name: "Quinn Murphy",     company: "Cortexia",          role: "VP of Product" },
  { name: "Rachel Baker",     company: "Launchpad Inc",     role: "Head of Engineering" },
  { name: "Samuel Carter",    company: "Gridline",          role: "CTO" },
  { name: "Tina Robinson",    company: "Wavelength Co",     role: "Director of Technology" },
];

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
      return !(l.name === lead.name && l.company === lead.company);
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
    const response = await fetch(`${API_URL}/outreach/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ leads: selectedLeads }),
    });

    if (response.ok) {
      const data = await response.json();
      renderResults(data.results);
    } else {
      renderError("Server error: " + response.status);
    }
  } catch (err) {
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
    header.textContent = item.lead;
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
