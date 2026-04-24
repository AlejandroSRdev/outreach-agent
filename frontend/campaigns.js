import { ALLOWED_INDUSTRIES, ALLOWED_TAGS } from "./constants.js";
import { createCampaign, CampaignApiError } from "./campaigns-api.js";

document.addEventListener("DOMContentLoaded", initCampaignSection);

function initCampaignSection() {
  const industrySelect = document.getElementById("industry-select");
  const tagsContainer = document.getElementById("tags-container");
  const submitBtn = document.getElementById("create-campaign-btn");

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select an industry";
  placeholder.disabled = true;
  placeholder.selected = true;
  industrySelect.appendChild(placeholder);

  for (const industry of ALLOWED_INDUSTRIES) {
    const option = document.createElement("option");
    option.value = industry;
    option.textContent = industry;
    industrySelect.appendChild(option);
  }

  for (const tag of ALLOWED_TAGS) {
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = tag;
    input.id = "tag-" + tag;

    const label = document.createElement("label");
    label.htmlFor = "tag-" + tag;
    label.textContent = tag;

    tagsContainer.appendChild(input);
    tagsContainer.appendChild(label);
  }

  industrySelect.addEventListener("change", () => {
    submitBtn.disabled = industrySelect.value === "";
  });

  submitBtn.addEventListener("click", submitCampaign);
}

async function submitCampaign() {
  const industrySelect = document.getElementById("industry-select");
  const tagsContainer = document.getElementById("tags-container");
  const submitBtn = document.getElementById("create-campaign-btn");
  const resultDiv = document.getElementById("campaign-result");

  const industry = industrySelect.value;

  const checkedInputs = tagsContainer.querySelectorAll("input[type='checkbox']:checked");
  const tagValues = Array.from(checkedInputs).map((input) => input.value);
  const tags = tagValues.length > 0 ? tagValues : null;

  submitBtn.disabled = true;
  submitBtn.textContent = "Creating...";
  resultDiv.innerHTML = "";

  try {
    const result = await createCampaign(industry, tags);
    const msg = document.createElement("div");
    msg.textContent = "Campaign #" + result.campaign_id + " created — " + result.total_leads + " leads";
    resultDiv.appendChild(msg);
  } catch (err) {
    const msg = document.createElement("div");
    msg.textContent = err instanceof CampaignApiError ? err.message : "Unexpected error";
    resultDiv.appendChild(msg);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Create Campaign";
    if (industrySelect.value === "") {
      submitBtn.disabled = true;
    }
  }
}
