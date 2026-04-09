const API = "http://localhost:5000";

async function sendData() {
  const sensor_id = document.getElementById("sensorId").value;
  const values = document.getElementById("values").value
    .split(",")
    .map((v) => Number(v.trim()))
    .filter((v) => Number.isFinite(v));

  const response = await fetch(`${API}/data`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sensor_id, values }),
  });

  const data = await response.json();
  document.getElementById("submitResult").textContent = JSON.stringify(data, null, 2);
}

async function getSummary() {
  const id = document.getElementById("dataId").value;
  const response = await fetch(`${API}/summary?id=${encodeURIComponent(id)}`);
  const data = await response.json();
  document.getElementById("summaryResult").textContent = JSON.stringify(data, null, 2);
}

async function listAll() {
  const response = await fetch(`${API}/list`);
  const data = await response.json();
  document.getElementById("listResult").textContent = JSON.stringify(data, null, 2);
}

document.getElementById("sendBtn").addEventListener("click", sendData);
document.getElementById("summaryBtn").addEventListener("click", getSummary);
document.getElementById("listBtn").addEventListener("click", listAll);
