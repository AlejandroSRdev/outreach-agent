const API_URL = import.meta.env.VITE_API_URL;

export class CampaignApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.message = message;
  }
}

export async function createCampaign(industry, tags) {
  let response;

  try {
    response = await fetch(`${API_URL}/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ industry, tags }),
    });
  } catch {
    throw new CampaignApiError(0, "Backend unreachable");
  }

  if (response.status === 201) {
    return await response.json();
  }

  if (response.status === 400) {
    throw new CampaignApiError(400, "No leads matched for these filters");
  }

  if (response.status === 422) {
    throw new CampaignApiError(422, "Invalid filter values");
  }

  throw new CampaignApiError(response.status, "Unexpected error (status: " + response.status + ")");
}
