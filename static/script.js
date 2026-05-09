document.addEventListener('DOMContentLoaded', async () => {
    let API_URL = 'http://127.0.0.1:5000'; // Default fallback

    try {
        const configResponse = await fetch('/config');
        if (configResponse.ok) {
            const config = await configResponse.json();
            API_URL = config.FRONTEND_API_URL;
        } else {
            console.warn('Could not fetch API URL from /config, using default.');
        }
    } catch (error) {
        console.error('Error fetching config:', error);
        Toastify({
            text: "Failed to load API configuration. Using default URL.",
            duration: 3000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: "linear-gradient(to right, #ff416c, #ff4b2b)",
        }).showToast();
    }

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');

    // Helper function for showing toasts
    const showToast = (message, isSuccess = true) => {
        Toastify({
            text: message,
            duration: 3000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: isSuccess ? "linear-gradient(to right, #00b09b, #96c93d)" : "linear-gradient(to right, #ff416c, #ff4b2b)",
        }).showToast();
    };



    // --- Form Handling ---
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Registering...';

            const formData = new FormData(registerForm);
            const data = Object.fromEntries(formData.entries());

            if (data.password !== data.confirm_password) {
                showToast('Passwords do not match.', false);
                submitBtn.disabled = false;
                submitBtn.innerText = 'Register';
                return;
            }
            delete data.confirm_password;

            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                showToast(result.message, response.ok);
                if (response.ok) {
                    window.location.href = '/';
                }
            } catch (error) {
                console.error('Registration error:', error);
                showToast('An error occurred during registration.', false);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Register';
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Logging in...';

            const formData = new FormData(loginForm);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (response.ok) {
                    localStorage.setItem('username', result.user.username);
                    window.location.href = `dashboard.html`;
                } else {
                    showToast(result.message, false);
                }
            } catch (error) {
                console.error('Login error:', error);
                showToast('An error occurred during login.', false);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Login';
            }
        });
    }

    if (window.location.pathname.includes('dashboard.html')) {
        const username = localStorage.getItem('username') || 'User';
        document.getElementById('usernameDisplay').innerText = username;

        const loadProfile = async () => {
            if (!username || username === 'User') {
                console.warn('Username not found or invalid.');
                return;
            }
            try {
                const response = await fetch(`/api/profile?username=${username}`);
                if (!response.ok) throw new Error('Failed to load profile');
                const user = await response.json();

                // Update User Card
                const avatarEl = document.getElementById('profile-avatar');
                if (avatarEl) avatarEl.innerText = user.fullname.charAt(0).toUpperCase();

                const fullnameEl = document.getElementById('profile-fullname');
                if (fullnameEl) fullnameEl.innerText = user.fullname;

                const usernameEl = document.getElementById('profile-username');
                if (usernameEl) usernameEl.innerText = `@${user.username}`;

                const emailEl = document.getElementById('profile-email');
                if (emailEl) emailEl.innerText = user.email;

                const genderAgeEl = document.getElementById('profile-gender-age');
                if (genderAgeEl) genderAgeEl.innerText = `${user.gender}, ${user.age} years old`;

                // Update Personal Info
                const workEl = document.getElementById('profile-work');
                if (workEl) workEl.innerText = user.work_type;

                const residenceEl = document.getElementById('profile-residence');
                if (residenceEl) residenceEl.innerText = user.residence_type;

                const maritalEl = document.getElementById('profile-marital');
                if (maritalEl) maritalEl.innerText = user.ever_married;

                const smokingEl = document.getElementById('profile-smoking');
                if (smokingEl) smokingEl.innerText = user.smoking_status;

                // Update Health Metrics
                const bmiEl = document.getElementById('profile-bmi');
                if (bmiEl) bmiEl.innerText = `${user.bmi.toFixed(1)} kg/m²`;

                const bmiStatus = document.getElementById('status-bmi');
                if (bmiStatus) {
                    if (user.bmi < 18.5) { bmiStatus.innerText = 'Underweight'; bmiStatus.style.color = 'var(--warning-color)'; }
                    else if (user.bmi < 25) { bmiStatus.innerText = 'Normal'; bmiStatus.style.color = 'var(--success-color)'; }
                    else { bmiStatus.innerText = 'Overweight'; bmiStatus.style.color = 'var(--danger-color)'; }
                }

                const glucoseEl = document.getElementById('profile-glucose');
                if (glucoseEl) glucoseEl.innerText = `${user.avg_glucose_level.toFixed(1)} mg/dL`;

                const glucoseStatus = document.getElementById('status-glucose');
                if (glucoseStatus) {
                    if (user.avg_glucose_level > 140) { glucoseStatus.innerText = 'High'; glucoseStatus.style.color = 'var(--danger-color)'; }
                    else { glucoseStatus.innerText = 'Normal'; glucoseStatus.style.color = 'var(--success-color)'; }
                }

                const hyperEl = document.getElementById('profile-hypertension');
                if (hyperEl) hyperEl.innerText = user.hypertension ? 'Yes' : 'No';

                const hyperStatus = document.getElementById('status-hypertension');
                if (hyperStatus) {
                    if (user.hypertension) { hyperStatus.innerText = 'Risk'; hyperStatus.style.color = 'var(--danger-color)'; }
                    else { hyperStatus.innerText = 'Normal'; hyperStatus.style.color = 'var(--success-color)'; }
                }

                const heartEl = document.getElementById('profile-heart-disease');
                if (heartEl) heartEl.innerText = user.heart_disease ? 'Yes' : 'No';

                const heartStatus = document.getElementById('status-heart-disease');
                if (heartStatus) {
                    if (user.heart_disease) { heartStatus.innerText = 'Risk'; heartStatus.style.color = 'var(--danger-color)'; }
                    else { heartStatus.innerText = 'Healthy'; heartStatus.style.color = 'var(--success-color)'; }
                }

            } catch (error) {
                console.error('Error loading profile:', error);
                showToast('Failed to load profile data', false);
            }
        };

        const loadPredictPage = async () => {
            if (!username || username === 'User') return;

            try {
                const response = await fetch(`/api/profile?username=${username}`);
                if (!response.ok) throw new Error('Failed to load profile for prediction');
                const user = await response.json();

                // Pre-fill form fields
                const setVal = (id, val) => {
                    const el = document.getElementById(id);
                    if (el) el.value = val;
                };

                setVal('predict-age', user.age);
                setVal('predict-gender', user.gender);
                setVal('predict-bmi', user.bmi.toFixed(1));
                setVal('predict-glucose', user.avg_glucose_level.toFixed(1));
                setVal('predict-hypertension', user.hypertension ? '1' : '0');
                setVal('predict-heart-disease', user.heart_disease ? '1' : '0');
                setVal('predict-work', user.work_type);
                setVal('predict-residence', user.residence_type);
                setVal('predict-smoking', user.smoking_status);
                setVal('predict-ever-married', user.ever_married);

            } catch (error) {
                console.error('Error loading predict page data:', error);
                showToast('Failed to load profile data for prediction', false);
            }
        };

        // --- Page Navigation (Moved here for scope access) ---
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.getAttribute('data-page');

                if (page) {
                    pages.forEach(p => p.classList.remove('active'));
                    document.getElementById(`${page}-page`).classList.add('active');

                    navItems.forEach(n => n.classList.remove('active'));
                    item.classList.add('active');

                    if (page === 'profile' && typeof loadProfile === 'function') {
                        loadProfile();
                    } else if (page === 'predict' && typeof loadPredictPage === 'function') {
                        loadPredictPage();
                    }
                }
            });
        });

        const hrCtx = document.getElementById('hrChart').getContext('2d');
        const spo2Ctx = document.getElementById('spo2Chart').getContext('2d');

        let sensorDisconnected = true;
        let autoPredictIntervalId;

        const createChart = (ctx, label, color) => {
            return new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [], // Start with empty labels
                    datasets: [{
                        label: label,
                        data: [], // Start with empty data
                        borderColor: color,
                        backgroundColor: `${color}1A`, // Add alpha for background
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: color,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            min: 0, // Ensure y-axis never goes below 0
                            grid: {
                                color: 'rgba(0,0,0,0.08)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.08)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        };

        const hrChart = createChart(hrCtx, 'Heart Rate', '#FF6E9A');
        const spo2Chart = createChart(spo2Ctx, 'SpO₂', '#3B82F6');

        const updateChart = (chart, value) => {
            const data = chart.data.datasets[0].data;
            const labels = chart.data.labels;

            // Add new data and timestamp
            const now = new Date();
            const timeString = [now.getHours(), now.getMinutes(), now.getSeconds()].map(n => n.toString().padStart(2, '0')).join(':');
            labels.push(timeString);
            data.push(value);

            // Keep only the last 10 data points
            if (data.length > 10) {
                data.shift();
                labels.shift();
            }

            // Dynamic Y-axis scaling with padding
            if (data.length > 0) {
                const maxVal = Math.max(...data);
                const minVal = Math.min(...data);
                const padding = (maxVal - minVal) * 0.1 || 5; // 10% padding, or a fallback of 5

                chart.options.scales.y.suggestedMax = maxVal + padding;
                // Ensure min is not negative and has padding
                chart.options.scales.y.suggestedMin = Math.max(0, minVal - padding);
            }

            chart.update('none');
        };

        const updateVitals = (type, value) => {
            const valueEl = document.getElementById(`${type}-value`);
            const alertEl = document.getElementById(`${type}-alert`);
            const cardEl = document.getElementById(`${type}-card`);

            valueEl.innerText = value;

            if (type === 'hr') {
                if (value < 50 || value > 120) {
                    alertEl.innerHTML = '&#9888; Abnormal Heart Rate';
                    alertEl.classList.add('danger');
                } else {
                    alertEl.innerText = 'Stable';
                    alertEl.classList.remove('danger');
                }
            } else if (type === 'spo2') {
                if (value < 92) {
                    alertEl.innerHTML = '&#9888; Low Blood Oxygen';
                    alertEl.classList.add('danger');
                } else {
                    alertEl.innerText = 'Stable';
                    alertEl.classList.remove('danger');
                }
            }
        };

        const updateOverallStatus = (status, resultText = '') => {
            const overallStatusEl = document.getElementById('overall-status');
            const overallStatusCard = document.getElementById('overall-status-card');

            if (overallStatusCard && overallStatusEl) {
                overallStatusCard.classList.remove('danger', 'normal', 'warning');

                switch (status) {
                    case 'danger':
                        overallStatusEl.innerText = 'Dangerous';
                        overallStatusCard.classList.add('danger');
                        break;
                    case 'normal':
                        overallStatusEl.innerText = 'Normal';
                        overallStatusCard.classList.add('normal');
                        break;
                    case 'warning':
                        overallStatusEl.innerText = resultText || 'No Prediction';
                        overallStatusCard.classList.add('warning');
                        break;
                    case 'error':
                        overallStatusEl.innerText = resultText || 'Error';
                        overallStatusCard.classList.add('danger');
                        break;
                }
            }
        };

        window.addToHistory = (result, probability, hr_value, spo2_value) => {
            const tbody = document.getElementById('history-tbody');
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>${new Date().toLocaleString()}</td>
                <td>${hr_value}</td>
                <td>${spo2_value}</td>
                <td>${result}</td>
                <td>${(probability * 100).toFixed(0)}%</td>
            `;
            tbody.prepend(newRow);
        };

        const autoPredict = async () => {
            if (sensorDisconnected) return;

            try {
                const heart_rate_el = document.getElementById('hr-value');
                const spo2_el = document.getElementById('spo2-value');

                if (!heart_rate_el || !spo2_el) return;

                const heart_rate = heart_rate_el.innerText;
                const spo2 = spo2_el.innerText;

                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, heart_rate: parseFloat(heart_rate), spo2: parseFloat(spo2) })
                });

                const result = await response.json();
                const aiResultDiv = document.getElementById('ai_result');
                const resultTextEl = document.getElementById('auto-ai-result-text');
                const confidenceEl = document.getElementById('auto-ai-confidence');
                const hrUsedEl = document.getElementById('auto-hr-used');
                const spo2UsedEl = document.getElementById('auto-spo2-used');
                const timestampEl = document.getElementById('auto-ai-timestamp');

                if (response.ok) {
                    if (resultTextEl) resultTextEl.innerText = result.result;

                    // Calculate confidence: if Normal, it's (1 - stroke_prob)
                    let strokeProb = parseFloat(result.probability);
                    let confidence = strokeProb;
                    if (result.result === 'Bình thường') {
                        confidence = 1 - strokeProb;
                    }
                    if (confidenceEl) confidenceEl.innerText = `${(confidence * 100).toFixed(0)}%`;
                    if (hrUsedEl) hrUsedEl.innerText = result.heart_rate;
                    if (spo2UsedEl) spo2UsedEl.innerText = result.spo2;
                    if (timestampEl) timestampEl.innerText = new Date().toLocaleTimeString();

                    if (aiResultDiv) {
                        aiResultDiv.style.color = result.result === 'Nguy cơ đột quỵ' ? 'var(--danger-color)' : 'var(--success-color)';
                    }

                    updateOverallStatus(result.result === 'Nguy cơ đột quỵ' ? 'danger' : 'normal');
                    addToHistory(result.result, result.probability, result.heart_rate, result.spo2);
                } else {
                    const errorData = await response.json();
                    console.error('Prediction failed:', errorData);
                    if (resultTextEl) resultTextEl.innerText = 'Error';
                    updateOverallStatus('error', errorData.message);
                }
            } catch (error) {
                console.error('Auto-prediction error:', error);
                const resultTextEl = document.getElementById('auto-ai-result-text');
                if (resultTextEl) resultTextEl.innerText = 'Error';
                updateOverallStatus('error', error.message);
            }
        };

        const fetchSensorData = async () => {
            const sensorStatusEl = document.getElementById('sensor-connection-status');
            const aiResultDiv = document.getElementById('ai_result');
            const resultTextEl = document.getElementById('auto-ai-result-text');

            try {
                const response = await fetch('/sensor-data');
                const data = await response.json();
                const secondsAgo = data.seconds_ago;

                const newHr = data.heart_rate || 0;
                const newSpo2 = data.spo2 || 0;

                if (secondsAgo === null || secondsAgo > 10) {
                    if (!sensorDisconnected) {
                        sensorDisconnected = true;
                        if (sensorStatusEl) {
                            sensorStatusEl.innerText = 'Disconnected ●';
                            sensorStatusEl.style.color = 'var(--danger-color)';
                        }
                        if (aiResultDiv) aiResultDiv.style.color = 'var(--warning-color)';
                        if (resultTextEl) resultTextEl.innerText = '⚠️ Sensor Disconnected';

                        updateOverallStatus('warning', 'No Prediction');
                        showToast('Sensor Disconnected.', false);
                        clearInterval(autoPredictIntervalId);
                    }
                } else {
                    // Only update charts if data is fresh
                    updateChart(hrChart, newHr);
                    updateChart(spo2Chart, newSpo2);
                    updateVitals('hr', newHr);
                    updateVitals('spo2', newSpo2);

                    if (sensorDisconnected) {
                        sensorDisconnected = false;
                        if (sensorStatusEl) {
                            sensorStatusEl.innerText = 'Connected ●';
                            sensorStatusEl.style.color = 'var(--success-color)';
                        }
                        showToast('Sensor Reconnected!', true);
                        // Restart auto-predict
                        autoPredictIntervalId = setInterval(autoPredict, 2000);
                    }
                }
            } catch (error) {
                console.error('Error fetching sensor data:', error);
                if (!sensorDisconnected) {
                    sensorDisconnected = true;
                    clearInterval(autoPredictIntervalId);

                    if (sensorStatusEl) {
                        sensorStatusEl.innerText = 'Disconnected ●';
                        sensorStatusEl.style.color = 'var(--danger-color)';
                    }
                    if (aiResultDiv) aiResultDiv.style.color = 'var(--warning-color)';
                    if (resultTextEl) resultTextEl.innerText = '⚠️ Sensor Disconnected';

                    updateOverallStatus('warning', 'No Prediction');
                    showToast('Sensor Disconnected.', false);
                }
            }
        };

        // --- Edit Profile Modal Logic ---
        const modal = document.getElementById('edit-profile-modal');
        const btn = document.getElementById('edit-profile-btn');
        const span = document.getElementsByClassName('close-modal')[0];
        const cancelBtn = document.querySelector('.close-modal-btn');
        const editForm = document.getElementById('edit-profile-form');

        // Open Modal and Pre-fill data
        if (btn) {
            btn.onclick = async () => {
                modal.style.display = "flex";

                // Fetch current profile data to pre-fill
                try {
                    const response = await fetch(`/api/profile?username=${username}`);
                    if (response.ok) {
                        const user = await response.json();

                        document.getElementById('edit-age').value = user.age;
                        document.getElementById('edit-gender').value = user.gender;
                        document.getElementById('edit-bmi').value = user.bmi;
                        document.getElementById('edit-glucose').value = user.avg_glucose_level;
                        document.getElementById('edit-hypertension').value = user.hypertension;
                        document.getElementById('edit-heart-disease').value = user.heart_disease;
                        document.getElementById('edit-work-type').value = user.work_type;
                        document.getElementById('edit-residence-type').value = user.residence_type;
                        document.getElementById('edit-smoking-status').value = user.smoking_status;
                        document.getElementById('edit-ever-married').value = user.ever_married;
                    }
                } catch (error) {
                    console.error('Error fetching profile for edit:', error);
                    showToast('Failed to load profile data', false);
                }
            }
        }

        // Close Modal
        const closeModal = () => {
            modal.style.display = "none";
        }

        if (span) span.onclick = closeModal;
        if (cancelBtn) cancelBtn.onclick = closeModal;

        window.onclick = (event) => {
            if (event.target == modal) {
                closeModal();
            }
        }

        // Handle Form Submission
        if (editForm) {
            editForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const submitBtn = editForm.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.innerText = 'Saving...';

                const formData = new FormData(editForm);
                const data = Object.fromEntries(formData.entries());
                data.username = username; // Add username to identify user

                try {
                    const response = await fetch('/api/profile/update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showToast('Profile updated successfully', true);
                        closeModal();
                        loadProfile(); // Reload profile data on dashboard
                    } else {
                        showToast(result.message || 'Failed to update profile', false);
                    }
                } catch (error) {
                    console.error('Error updating profile:', error);
                    showToast('An error occurred while updating', false);
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Save Changes';
                }
            });
        }

        const manualPredictForm = document.getElementById('manual-predict-form');
        if (manualPredictForm) {
            manualPredictForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const submitBtn = manualPredictForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Processing...';

                const formData = new FormData(manualPredictForm);
                const data = Object.fromEntries(formData.entries());

                // Add username and ensure numeric types
                data.username = localStorage.getItem('username');
                data.heart_rate = parseFloat(data.heart_rate);
                data.spo2 = parseFloat(data.spo2);
                data.age = parseFloat(data.age);
                data.bmi = parseFloat(data.bmi);
                data.avg_glucose_level = parseFloat(data.avg_glucose_level);
                data.hypertension = parseInt(data.hypertension);
                data.heart_disease = parseInt(data.heart_disease);

                try {
                    const response = await fetch(`${API_URL}/predict`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });

                    const result = await response.json();
                    const outputDiv = document.getElementById('manual-prediction-output');

                    if (response.ok) {
                        // Calculate confidence
                        let strokeProb = parseFloat(result.probability);
                        let confidence = strokeProb;
                        if (result.result === 'Bình thường') {
                            confidence = 1 - strokeProb;
                        }
                        const confidencePercent = (confidence * 100).toFixed(0);
                        const isHighRisk = result.result === 'Nguy cơ đột quỵ';

                        // Update card border
                        const resultCard = document.querySelector('.predict-result-card');
                        resultCard.classList.remove('success-border', 'danger-border');
                        resultCard.classList.add(isHighRisk ? 'danger-border' : 'success-border');

                        const timestamp = new Date().toLocaleString();

                        outputDiv.innerHTML = `
                            <div class="status-box ${isHighRisk ? 'danger' : 'success'}">
                                ${isHighRisk ?
                                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>' :
                                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
                            }
                                <div>
                                    <span class="status-title">${isHighRisk ? 'High Stroke Risk Detected' : 'Normal Risk Level'}</span>
                                    <span class="status-message">${isHighRisk ? 'Immediate medical consultation recommended' : 'Continue maintaining healthy lifestyle'}</span>
                                </div>
                            </div>

                            <div class="result-content-grid">
                                <div class="probability-chart-container" style="margin-bottom: 0;">
                                    <svg viewBox="0 0 36 36" class="circular-chart" style="max-width: 120px; max-height: 120px;">
                                        <path class="circle-bg"
                                            d="M18 2.0845
                                            a 15.9155 15.9155 0 0 1 0 31.831
                                            a 15.9155 15.9155 0 0 1 0 -31.831"
                                        />
                                        <path class="circle"
                                            stroke-dasharray="${confidencePercent}, 100"
                                            d="M18 2.0845
                                            a 15.9155 15.9155 0 0 1 0 31.831
                                            a 15.9155 15.9155 0 0 1 0 -31.831"
                                        />
                                        <text x="18" y="20.35" class="percentage">${confidencePercent}%</text>
                                        <text x="18" y="25" class="percentage-label">Confidence</text>
                                    </svg>
                                </div>

                                <div class="result-metrics">
                                    <div class="metric-row">
                                        <span class="metric-label">Risk Level</span>
                                        <span class="metric-value ${isHighRisk ? 'danger-text' : 'success-text'}">${isHighRisk ? 'High' : 'Normal'}</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Heart Rate</span>
                                        <span class="metric-value">${result.heart_rate} bpm</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">SpO₂</span>
                                        <span class="metric-value">${result.spo2}%</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Timestamp</span>
                                        <span class="metric-value">${timestamp}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="recommendation-section">
                                <div class="recommendation-title">
                                    ${isHighRisk ?
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D69E2E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg> Recommended Actions:' :
                                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg> Continue To:'
                            }
                                </div>
                                <ul class="recommendation-list">
                                    ${isHighRisk ?
                                `<li>Consult healthcare provider immediately</li>
                                         <li>Monitor vital signs closely</li>
                                         <li>Follow prescribed medication regimen</li>
                                         <li>Reduce risk factors (diet, exercise)</li>` :
                                `<li>Maintain regular exercise routine</li>
                                         <li>Follow balanced, healthy diet</li>
                                         <li>Schedule regular health checkups</li>
                                         <li>Monitor vital signs periodically</li>`
                            }
                                </ul>
                            </div>

                            <div class="disclaimer-text" style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; font-size: 12px; color: #9CA3AF; line-height: 1.5;">
                                <strong>Disclaimer:</strong> This AI prediction is for informational purposes only and does not constitute a medical diagnosis. Please consult with a qualified healthcare professional for any medical concerns.
                            </div>
                        `;
                        showToast('Prediction complete', true);
                    } else {
                        showToast(result.message || 'Prediction failed', false);
                    }
                } catch (error) {
                    console.error('Manual prediction error:', error);
                    showToast('An error occurred during prediction', false);
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
            });
        }

        setInterval(fetchSensorData, 2500);
    }
});
