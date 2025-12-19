const API_URL = 'http://localhost:8000';
let statusInterval = null;

async function runAgent() {
    const role = document.getElementById('role').value;
    const location = document.getElementById('location').value;
    const rss_url = document.getElementById('rss-url').value;
    const btn = document.getElementById('run-btn');

    if (!role || !location) {
        alert("Please enter both role and location");
        return;
    }

    try {
        btn.disabled = true;
        btn.innerText = "Launching...";

        // Create FormData to handle file upload
        const formData = new FormData();
        formData.append('role', role);
        formData.append('location', location);
        if (rss_url) formData.append('rss_url', rss_url);
        if (window.uploadedResume) formData.append('resume', window.uploadedResume);

        const response = await fetch(`${API_URL}/run`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            logActivity("Agent process started.");
            startStatusPolling();
        } else {
            console.error("Failed to start agent");
            btn.disabled = false;
        }
    } catch (e) {
        console.error(e);
        btn.disabled = false;
    }
}

function startStatusPolling() {
    document.getElementById('progress-container').classList.remove('hidden');
    if (statusInterval) clearInterval(statusInterval);

    statusInterval = setInterval(async () => {
        try {
            const resp = await fetch(`${API_URL}/status`);
            const data = await resp.json();

            updateUI(data);

            if (!data.is_running && data.current_step === "Completed") {
                clearInterval(statusInterval);
                logActivity("Run finished successfully.");
                document.getElementById('run-btn').disabled = false;
                document.getElementById('run-btn').innerText = "Run Agent";
                fetchJobs();
            } else if (data.current_step.startsWith("Error")) {
                clearInterval(statusInterval);
                logActivity(data.current_step);
                document.getElementById('run-btn').disabled = false;
                document.getElementById('run-btn').innerText = "Run Agent";
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 2000);
}

function updateUI(status) {
    const progressBar = document.getElementById('progress-bar');
    const progressValue = document.getElementById('progress-value');
    const stepLabel = document.getElementById('current-step-label');
    const badge = document.getElementById('status-badge');

    progressBar.style.width = `${status.progress}%`;
    progressValue.innerText = `${status.progress}%`;
    stepLabel.innerText = status.current_step;

    if (status.is_running) {
        badge.innerText = "Agent Running";
        badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-cyan-900/30 text-cyan-400 border border-cyan-800/30";
    } else {
        badge.innerText = "System Idle";
        badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-gray-900 text-gray-400 border border-gray-800";
    }

    logActivity(status.current_step);
}

const lastStep = "";
function logActivity(step) {
    if (step === lastStep || step === "Idle") return;
    const log = document.getElementById('activity-log');
    const div = document.createElement('div');
    div.className = "flex gap-3 text-xs text-gray-400 border-l border-blue-500/50 pl-4 py-2 transition-all opacity-0 translate-y-2";
    div.innerText = `${new Date().toLocaleTimeString()} - ${step}`;
    log.prepend(div);
    setTimeout(() => {
        div.classList.remove('opacity-0', 'translate-y-2');
    }, 10);
}

async function fetchJobs() {
    const statusFilter = document.getElementById('filter-status').value;
    try {
        const response = await fetch(`${API_URL}/jobs?status=${statusFilter}`);
        const jobs = await response.json();
        renderJobs(jobs);
    } catch (e) {
        console.error("Failed to fetch jobs", e);
    }
}

function renderJobs(jobs) {
    const list = document.getElementById('job-list');

    // Calculate statistics
    const totalJobs = jobs.length;
    const contactsFound = jobs.filter(j => j.contact_email).length;
    const emailsDrafted = jobs.filter(j => j.status === 'drafted').length;

    // Update stats
    document.getElementById('stat-jobs').textContent = totalJobs;
    document.getElementById('stat-contacts').textContent = contactsFound;
    document.getElementById('stat-emails').textContent = emailsDrafted;

    if (jobs.length === 0) {
        list.innerHTML = '<div class="text-center py-20 text-gray-600"><div class="text-6xl mb-4 animate-float">🔍</div><p>No jobs found yet. Launch a search to get started!</p></div>';
        return;
    }

    list.innerHTML = jobs.map(job => `
        <div class="glass border border-gray-900 p-6 rounded-xl hover:border-cyan-900/50 transition-all group">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-lg font-semibold group-hover:text-cyan-400 transition-colors">${job.title}</h3>
                    <p class="text-xs text-gray-500 mt-1">${job.company} • ${job.location}</p>
                </div>
                <div class="${getScoreClass(job.score)} px-2 py-1 rounded text-[10px] font-bold">
                    SCORE: ${job.score || 'N/A'}
                </div>
            </div>
            <div class="flex gap-2 flex-wrap">
                <span class="px-2 py-1 bg-gray-900 border border-gray-800 rounded text-[10px] text-gray-400">${job.status.toUpperCase()}</span>
                ${job.contact_email ? '<span class="px-2 py-1 bg-green-900/20 border border-green-800/40 rounded text-[10px] text-green-400">✓ CONTACT FOUND</span>' : ''}
                <a href="${job.url}" target="_blank" class="text-[10px] text-cyan-500 ml-auto hover:underline">View Post ↗</a>
            </div>
            ${job.match_reasons ? `<p class="mt-4 text-xs text-gray-400 italic font-light line-clamp-2">" ${job.match_reasons} "</p>` : ''}
        </div>
    `).join('');
}

function getScoreClass(score) {
    if (score >= 8) return 'bg-green-900/30 text-green-400 border border-green-800/30';
    if (score >= 5) return 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/30';
    return 'bg-red-900/30 text-red-400 border border-red-800/30';
}

// Initial fetch
fetchJobs();
setInterval(fetchJobs, 10000); // Periodic refresh
