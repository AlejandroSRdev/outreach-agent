const API_URL = import.meta.env.VITE_API_URL;

let leads = [];
const leadById = {};

let selectedLeads = [];
let activeCampaignId = null;
let isLoading = false;
let pollingInterval = null;
let pendingExecutionData = null;

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
  const runBtn = document.getElementById("run-btn");
  const showResultsBtn = document.getElementById("show-results-btn");
  const statusMsg = document.getElementById("status-msg");
  const resultsContainer = document.getElementById("results-container");

  runBtn.disabled = true;
  showResultsBtn.disabled = true;
  resultsContainer.innerHTML = "";
  pendingExecutionData = null;
  stopPolling();
  statusMsg.textContent = "Starting execution...";

  let response;
  try {
    response = await fetch(`${API_URL}/outreach/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ campaign_id: activeCampaignId }),
    });
  } catch (err) {
    renderError("Network error — backend unreachable");
    runBtn.disabled = false;
    statusMsg.textContent = "";
    return;
  }

  if (!response.ok) {
    renderError("Server error: " + response.status);
    runBtn.disabled = false;
    statusMsg.textContent = "";
    return;
  }

  const data = await response.json();
  statusMsg.textContent = "Execution started — " + data.total_leads + " leads queued";
  startPolling(data.execution_id);
}

function startPolling(executionId) {
  pollingInterval = setInterval(async function () {
    let response;
    try {
      response = await fetch(`${API_URL}/executions/${executionId}`);
    } catch (err) {
      stopPolling();
      renderError("Network error while polling");
      document.getElementById("run-btn").disabled = false;
      return;
    }

    if (!response.ok) {
      stopPolling();
      renderError("Failed to check execution: " + response.status);
      document.getElementById("run-btn").disabled = false;
      return;
    }

    const data = await response.json();
    document.getElementById("status-msg").textContent =
      "Processing... (" + (data.completed_leads + data.failed_leads) + "/" + data.total_leads + " leads done)";

    if (data.status === "completed" || data.status === "failed") {
      stopPolling();
      pendingExecutionData = data;
      document.getElementById("show-results-btn").disabled = false;
      document.getElementById("run-btn").disabled = false;
      document.getElementById("status-msg").textContent = "Execution " + data.status + " — click Show Results";
    }
  }, 3000);
}

function stopPolling() {
  if (pollingInterval !== null) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

function showResults() {
  if (pendingExecutionData === null) return;
  document.getElementById("results-container").innerHTML = "";
  renderResults(pendingExecutionData.leads);
}

function renderResults(leads) {
  const container = document.getElementById("results-container");

  leads.forEach(function (item) {
    const block = document.createElement("div");
    block.className = "result-block";

    const header = document.createElement("div");
    header.className = "result-header";
    header.textContent = item.name;
    block.appendChild(header);

    if (item.email) {
      const emailLine = document.createElement("div");
      emailLine.className = "result-email";
      emailLine.textContent = "Email: " + item.email;
      block.appendChild(emailLine);
    }

    const statusLine = document.createElement("div");
    if (item.status === "completed") {
      statusLine.className = "status-success";
      statusLine.textContent = "Status: success";
    } else {
      statusLine.className = "status-failed";
      statusLine.textContent = "Status: failed";
    }
    block.appendChild(statusLine);

    if (item.status === "completed" && item.output !== null) {
      const subjectLine = document.createElement("div");
      subjectLine.className = "result-subject";
      subjectLine.textContent = "Subject: " + item.output.subject;
      block.appendChild(subjectLine);

      const textarea = document.createElement("textarea");
      textarea.readOnly = true;
      textarea.value = item.output.body;
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
document.getElementById("show-results-btn").addEventListener("click", showResults);
fetchLeads();
