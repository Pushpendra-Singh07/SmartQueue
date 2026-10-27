const POLL_MS = 4000;

function doctorId() {
    const select = document.getElementById("doctor-select");
    const box = document.getElementById("queue-container");
    if (select && select.value) return select.value;
    return box?.dataset.doctorId || "";
}

function render(entries) {
    const box = document.getElementById("queue-container");
    if (!entries.length) {
        box.innerHTML = '<p class="placeholder">No one is waiting.</p>';
        return;
    }
    const canAct = Boolean(document.getElementById("btn-call-next"));
    box.innerHTML = entries.map((entry) => `
        <div class="queue-item ${entry.priority === "Emergency" ? "emergency" : ""}">
            <div>
                <div class="token">${entry.token_no}</div>
                <div>${entry.patient.name} · ${entry.patient.age}y · ${entry.patient.gender}</div>
                <small>${entry.priority} · ${entry.status}</small>
            </div>
            ${canAct ? `<div class="actions">
                <button class="btn btn-sm" data-action="complete" data-id="${entry.id}" type="button">Done</button>
                <button class="btn btn-sm" data-action="no-show" data-id="${entry.id}" type="button">No Show</button>
            </div>` : ""}
        </div>`).join("");
}

async function refresh() {
    const id = doctorId();
    const box = document.getElementById("queue-container");
    if (!id) {
        box.innerHTML = '<p class="placeholder">No doctor selected.</p>';
        return;
    }
    const response = await fetch(`/api/queue/doctor/${id}`);
    if (response.ok) render(await response.json());
}

document.addEventListener("DOMContentLoaded", () => {
    if (!document.getElementById("queue-container")) return;
    refresh();
    setInterval(refresh, POLL_MS);
    document.getElementById("doctor-select")?.addEventListener("change", refresh);
    document.getElementById("btn-call-next")?.addEventListener("click", async () => {
        await fetch(`/api/queue/call-next/${doctorId()}`, { method: "POST" });
        refresh();
    });
    document.getElementById("queue-container").addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const action = button.dataset.action === "complete" ? "complete" : "no-show";
        await fetch(`/api/queue/${action}/${button.dataset.id}`, { method: "POST" });
        refresh();
    });
});
