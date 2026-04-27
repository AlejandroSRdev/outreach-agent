const API_URL = import.meta.env.VITE_API_URL;

let leads = [];
const leadById = {};

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
let activeCampaignId = null;
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
  leads.forEach(function (lead, index) {
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
    checkbox.checked = selectedLeads.some(function (l) { return l.id === lead.id; });
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
  runBtn.disabled = activeCampaignId === null || selectedLeads.length === 0;
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
      body: JSON.stringify({ campaign_id: activeCampaignId }),
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

async function fetchLeads() {
  try {
    const response = await fetch(`${API_URL}/leads`, { method: "GET" });

    if (response.ok) {
      const data = await response.json();
      leads = data;
      leads.forEach(function (lead) { leadById[lead.id] = lead; });
      renderTable();
    } else {
      renderError("Failed to load leads: " + response.status);
      document.getElementById("run-btn").disabled = true;
    }
  } catch (err) {
    renderError("Network error — could not load leads");
    document.getElementById("run-btn").disabled = true;
  }
}

function onCampaignCreated(event) {
  var lead_ids = event.detail.lead_ids;

  var matched = lead_ids
    .map(function (id) { return leadById[id]; })
    .filter(function (lead) { return lead !== undefined; })
    .slice(0, 20);

  selectedLeads = matched;
  activeCampaignId = event.detail.campaign_id;

  var container = document.getElementById("lead-table-container");
  container.innerHTML = "";
  renderTable();
  updateSelectionUI();
}

document.addEventListener("campaign-created", onCampaignCreated);

// Init
document.getElementById("run-btn").addEventListener("click", runBatch);
fetchLeads();
