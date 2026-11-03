<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#05080f">
    <title>FX PRO</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        :root {
            --bg-main: #05080f; --bg-card: #111625; --bg-element: #1a2035; --border: #1e293b;
            --text-main: #f8fafc; --text-muted: #64748b; --gold: #d4a843; --gold-glow: rgba(212, 168, 67, 0.15);
            --green: #10b981; --green-bg: rgba(16, 185, 129, 0.15); --red: #ef4444; --red-bg: rgba(239, 68, 68, 0.15);
            --blue: #3b82f6; --blue-bg: rgba(59, 130, 246, 0.15);
        }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-main); color: var(--text-main); display: flex; min-height: 100vh; }

        /* --- SIDEBAR (LAPTOP) --- */
        .sidebar { width: 240px; background: var(--bg-card); border-right: 1px solid var(--border); padding: 20px 0; position: fixed; height: 100vh; display: flex; flex-direction: column; }
        .logo { padding: 0 20px 20px; border-bottom: 1px solid var(--border); margin-bottom: 20px; font-size: 20px; font-weight: 900; color: var(--gold); letter-spacing: 1px; }
        .nav-item { padding: 12px 20px; color: var(--text-muted); font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: 0.2s; border-left: 3px solid transparent; }
        .nav-item:hover { background: var(--bg-element); color: var(--text-main); }
        .nav-item.active { background: var(--gold-glow); color: var(--gold); border-left-color: var(--gold); }
        .sidebar-footer { margin-top: auto; padding: 20px; font-size: 10px; color: var(--text-muted); border-top: 1px solid var(--border); }

        /* --- MAIN CONTENT --- */
        .main { margin-left: 240px; flex: 1; padding: 30px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; flex-wrap: wrap; gap: 15px; }
        .header-title { font-size: 24px; font-weight: 800; }
        .header-right { display: flex; align-items: center; gap: 15px; }
        .live-badge { background: var(--green-bg); color: var(--green); padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; display: flex; align-items: center; gap: 6px; }
        .live-dot { width: 6px; height: 6px; background: var(--green); border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .clock { font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }

        /* --- FILTERS --- */
        .filters { display: flex; gap: 8px; margin-bottom: 25px; overflow-x: auto; padding-bottom: 5px; }
        .filter-btn { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-muted); padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; transition: 0.2s; }
        .filter-btn:hover { border-color: var(--gold); }
        .filter-btn.active { background: var(--gold-glow); border-color: var(--gold); color: var(--gold); }

        /* --- GRID LAYOUT --- */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
        .pair-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
        .pair-name { font-size: 20px; font-weight: 800; }
        .count-badge { background: var(--bg-element); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; color: var(--gold); }

        .setup-block { background: var(--bg-element); border-radius: 8px; padding: 12px; margin-bottom: 10px; border: 1px solid var(--border); transition: all 0.3s; }
        .setup-block.live-block { border-color: var(--green); box-shadow: 0 0 15px rgba(16, 185, 129, 0.1); }
        
        .setup-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .tf-badge { background: var(--bg-card); padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; }
        .dir-badge { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; }
        .dir-badge.buy { background: var(--green-bg); color: var(--green); }
        .dir-badge.sell { background: var(--red-bg); color: var(--red); }
        .status-text { font-size: 10px; font-weight: 800; letter-spacing: 0.5px; }
        .status-text.active { color: var(--green); }
        .status-text.pending { color: var(--blue); }

        .strat-text { font-size: 11px; color: var(--text-muted); margin-bottom: 10px; font-style: italic; }
        .price-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 10px; }
        .price-cell { background: var(--bg-card); padding: 8px; border-radius: 6px; text-align: center; }
        .price-label { font-size: 8px; color: var(--text-muted); font-weight: 800; margin-bottom: 3px; }
        .price-val { font-size: 13px; font-weight: 700; font-family: monospace; }
        .price-val.entry { color: var(--gold); } .price-val.stop { color: var(--red); } .price-val.tp { color: var(--green); }

        .timer-track { height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }
        .timer-fill { height: 100%; background: var(--gold); transition: width 1s; }
        .timer-text { font-size: 10px; color: var(--text-muted); text-align: right; margin-top: 4px; }

        /* --- VIEWS --- */
        .view-section { display: none; }
        .view-section.active { display: block; }
        .placeholder-box { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 40px; text-align: center; color: var(--text-muted); }

        /* --- MOBILE BOTTOM NAV --- */
        .bottom-nav { display: none; position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg-card); border-top: 1px solid var(--border); padding: 10px 0 20px; z-index: 100; justify-content: space-around; }
        .mob-btn { display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--text-muted); font-size: 10px; font-weight: 600; cursor: pointer; }
        .mob-btn.active { color: var(--gold); }

        /* --- RESPONSIVE --- */
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .main { margin-left: 0; padding: 15px; padding-bottom: 80px; }
            .bottom-nav { display: flex; }
            .grid { grid-template-columns: 1fr; }
            .header { flex-direction: column; align-items: flex-start; }
        }
    </style>
</head>
<body>

    <!-- Laptop Sidebar -->
    <aside class="sidebar">
        <div class="logo">FX PRO</div>
        <div class="nav-item active" onclick="switchView('dashboard', this)">📊 Dashboard</div>
        <div class="nav-item" onclick="switchView('signals', this)">🎯 Signals</div>
        <div class="nav-item" onclick="switchView('journal', this)">📓 Journal</div>
        <div class="nav-item" onclick="switchView('settings', this)">⚙️ Settings</div>
        <div class="sidebar-footer">FX PRO STRATEGY<br>Educational use only. Not financial advice.</div>
    </aside>

    <!-- Main Content -->
    <main class="main">
        <!-- Dashboard View -->
        <div id="view-dashboard" class="view-section active">
            <div class="header">
                <div class="header-title">Market Signals</div>
                <div class="header-right">
                    <div class="live-badge"><div class="live-dot"></div> LIVE FEED</div>
                    <div class="clock" id="clock">00:00:00</div>
                </div>
            </div>

            <div class="filters">
                <button class="filter-btn active" onclick="filterSignals('all', this)">ALL</button>
                <button class="filter-btn" onclick="filterSignals('live', this)">LIVE</button>
                <button class="filter-btn" onclick="filterSignals('pending', this)">PENDING</button>
            </div>

            <div class="grid" id="signalGrid">
                <div class="placeholder-box">Scanning all timeframes for high-confluence setups...</div>
            </div>
        </div>

        <!-- Journal View -->
        <div id="view-journal" class="view-section">
            <div class="header"><div class="header-title">Trade Journal</div></div>
            <div class="placeholder-box"><h3 style="color: var(--text-main); margin-bottom: 10px;">Track Your Trades</h3><p>Log your entries, exits, and emotions here to improve your consistency.</p></div>
        </div>

        <!-- Settings View -->
        <div id="view-settings" class="view-section">
            <div class="header"><div class="header-title">Settings</div></div>
            <div class="placeholder-box"><h3 style="color: var(--text-main); margin-bottom: 10px;">App Preferences</h3><p>Manage notifications, risk parameters, and account details.</p></div>
        </div>
    </main>

    <!-- Mobile Bottom Nav -->
    <nav class="bottom-nav">
        <div class="mob-btn active" onclick="switchView('dashboard', this)">📊<div>Dashboard</div></div>
        <div class="mob-btn" onclick="switchView('signals', this)">🎯<div>Signals</div></div>
        <div class="mob-btn" onclick="switchView('journal', this)">📓<div>Journal</div></div>
        <div class="mob-btn" onclick="switchView('settings', this)">⚙️<div>Settings</div></div>
    </nav>

    <script>
        setInterval(() => { document.getElementById('clock').innerText = new Date().toTimeString().split(' ')[0]; }, 1000);

        function switchView(viewName, btn) {
            document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
            document.getElementById('view-' + viewName).classList.add('active');
            document.querySelectorAll('.nav-item, .mob-btn').forEach(b => b.classList.remove('active'));
            if(btn) btn.classList.add('active');
        }

        let currentFilter = 'all';
        function filterSignals(filter, btn) {
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderSignals(window.lastSignals || []); 
        }

        async function fetchSignals() {
            try {
                // ⚠️ REPLACE WITH YOUR ACTUAL RENDER URL ⚠️
                const res = await fetch('https://YOUR-RENDER-URL.onrender.com/signals');
                const signals = await res.json();
                window.lastSignals = signals;
                renderSignals(signals);
            } catch (e) {
                document.getElementById('signalGrid').innerHTML = `<div class="placeholder-box">⚠️ Backend Disconnected</div>`;
            }
        }

        function renderSignals(signals) {
            const grid = document.getElementById('signalGrid');
            if (!signals || signals.length === 0) {
                grid.innerHTML = `<div class="placeholder-box">📡 No active setups. AI is scanning all timeframes...</div>`;
                return;
            }

            let html = '';
            let globalIdx = 0;

            signals.forEach(s => {
                let filteredSetups = s.setups;
                
                // Filter logic based on Pending/Live status
                if (currentFilter === 'live') {
                    filteredSetups = s.setups.filter(setup => {
                        const isBuy = setup.direction === 'BUY';
                        return (isBuy && setup.current_price >= setup.entry) || (!isBuy && setup.current_price <= setup.entry);
                    });
                } else if (currentFilter === 'pending') {
                    filteredSetups = s.setups.filter(setup => {
                        const isBuy = setup.direction === 'BUY';
                        return (isBuy && setup.current_price < setup.entry) || (!isBuy && setup.current_price > setup.entry);
                    });
                }
                
                if (filteredSetups.length === 0) return;

                html += `<div class="pair-card">
                    <div class="card-header"><div class="pair-name">${s.pair}</div><div class="count-badge">${filteredSetups.length} SETUP${filteredSetups.length > 1 ? 'S' : ''}</div></div>`;
                
                filteredSetups.forEach(setup => {
                    const isBuy = setup.direction === 'BUY';
                    const uniqueId = `s-${globalIdx}`;
                    
                    // PENDING TO LIVE LOGIC
                    let status = 'pending';
                    let statusText = 'PENDING';
                    let blockClass = 'setup-block';

                    if ((isBuy && setup.current_price >= setup.entry) || (!isBuy && setup.current_price <= setup.entry)) {
                        status = 'active';
                        statusText = 'LIVE';
                        blockClass = 'setup-block live-block';
                    }

                    html += `<div class="${blockClass}">
                        <div class="setup-top">
                            <div style="display:flex; gap:6px;"><span class="tf-badge">${setup.timeframe}</span><span class="dir-badge ${isBuy ? 'buy' : 'sell'}">${setup.direction}</span></div>
                            <span class="status-text ${status}">● ${statusText}</span>
                        </div>
                        <div class="strat-text">${setup.strategy_name}</div>
                        <div class="price-grid">
                            <div class="price-cell"><div class="price-label">ENTRY</div><div class="price-val entry">${setup.entry}</div></div>
                            <div class="price-cell"><div class="price-label">STOP</div><div class="price-val stop">${setup.stopLoss}</div></div>
                            <div class="price-cell"><div class="price-label">TP1</div><div class="price-val tp">${setup.takeProfit}</div></div>
                        </div>
                        <div class="timer-track"><div class="timer-fill" id="fill-${uniqueId}" style="width:100%"></div></div>
                        <div class="timer-text" id="time-${uniqueId}">30:00</div>
                    </div>`;
                    globalIdx++;
                });
                html += `</div>`;
            });
            grid.innerHTML = html || `<div class="placeholder-box">No setups match this filter.</div>`;
            startTimers(globalIdx);
        }

        function startTimers(total) {
            for (let i = 0; i < total; i++) {
                const id = `s-${i}`;
                const exp = new Date(); exp.setMinutes(exp.getMinutes() + 30);
                setInterval(() => {
                    const diff = exp - new Date();
                    if (diff <= 0) { document.getElementById(`time-${id}`).innerText = "EXPIRED"; document.getElementById(`fill-${id}`).style.width = "0%"; return; }
                    const m = Math.floor(diff / 60000), s = Math.floor((diff % 60000) / 1000);
                    document.getElementById(`time-${id}`).innerText = `${m}:${s.toString().padStart(2, '0')}`;
                    document.getElementById(`fill-${id}`).style.width = `${(diff / 1800000) * 100}%`;
                }, 1000);
            }
        }

        fetchSignals();
        setInterval(fetchSignals, 60000);
    </script>
</body>
</html>
