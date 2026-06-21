import os
from flask import Flask, render_template_string, jsonify, request, Response
from datetime import datetime
from supabase import create_client, Client
import threading, time

app = Flask(__name__)

# === KONFIGURASI SUPABASE ===
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("WARNING: Kredensial Supabase belum diatur!")

# --- UI DASHBOARD SULTAN ---
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GateIntelligence - Command Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b1120; color: #f8fafc; overflow-x: hidden; }
        .bento-card { background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .bento-card:hover { border-color: rgba(59, 130, 246, 0.3); box-shadow: 0 10px 40px -10px rgba(59, 130, 246, 0.1); }
        .road-container { background: #1e293b; background-image: linear-gradient(90deg, transparent 48%, rgba(255,255,255,0.1) 48%, rgba(255,255,255,0.1) 52%, transparent 52%); background-size: 40px 100%; position: relative; overflow: hidden; }
        .gate-pivot { transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); transform-origin: top left; }
        .gate-closed { transform: rotate(0deg); }
        .gate-open { transform: rotate(-90deg); }
        .neon-glow { box-shadow: 0 0 15px currentColor; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-[#0b1120] to-black">
    <div class="max-w-[1400px] mx-auto flex flex-col gap-6">
        <header class="flex flex-col md:flex-row justify-between items-center gap-4 bento-card p-6">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                    <i class="fa-solid fa-cloud text-2xl text-white"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-300">GateIntelligence</h1>
                    <p class="text-slate-400 text-xs font-medium uppercase tracking-widest mt-1">Sistem Monitoring Terintegrasi Supabase</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <div class="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div> DB Online
                </div>
                <div class="px-4 py-2 rounded-lg bg-slate-800/80 border border-slate-700 font-mono text-sm font-bold text-slate-300 shadow-inner">
                    <i class="fa-regular fa-clock mr-2 text-blue-400"></i><span id="live-clock">00:00:00</span>
                </div>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
            <div class="md:col-span-12 lg:col-span-3 flex flex-col gap-6">
                <div class="bento-card p-6 relative overflow-hidden group">
                    <div class="absolute -right-6 -top-6 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all"></div>
                    <p class="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2">Total Kendaraan Masuk</p>
                    <div class="flex items-end justify-between">
                        <h3 id="ui-total" class="text-6xl font-black text-white tracking-tighter">0</h3>
                        <i class="fa-solid fa-car-side text-4xl text-blue-500/50 mb-2"></i>
                    </div>
                </div>

                <div class="bento-card p-6 flex-grow flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-4">
                            <p class="text-xs text-slate-400 font-semibold uppercase tracking-wider"><i class="fa-solid fa-satellite-dish mr-2 text-indigo-400"></i>Jarak Objek</p>
                            <span id="ui-dist-badge" class="text-[10px] px-2 py-1 rounded bg-slate-800 text-slate-300 font-bold">STANDBY</span>
                        </div>
                        <div class="flex items-baseline gap-1">
                            <h3 id="ui-distance" class="text-5xl font-black text-indigo-400 font-mono transition-colors duration-300">0</h3>
                            <span id="ui-dist-unit" class="text-slate-500 font-bold transition-opacity duration-300">cm</span>
                        </div>
                    </div>
                    <div class="mt-6">
                        <div class="w-full h-2 bg-slate-800 rounded-full overflow-hidden flex">
                            <div id="ui-dist-bar" class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 w-0 transition-all duration-100"></div>
                        </div>
                        <div class="flex justify-between text-[10px] text-slate-500 mt-2 font-mono">
                            <span>0cm</span><span>Limit (10cm)</span><span>Max</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="md:col-span-12 lg:col-span-6 flex flex-col gap-6">
                <div class="bento-card road-container h-48 rounded-3xl flex items-center justify-center border border-slate-700/50 shadow-inner">
                    <span class="absolute top-4 left-4 bg-black/50 backdrop-blur border border-white/10 text-slate-300 px-3 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider flex items-center gap-2 z-10">
                        <i class="fa-solid fa-video text-red-500 animate-pulse"></i> Live Top-Down View
                    </span>
                    <div class="relative w-full max-w-[200px] flex items-center justify-center">
                        <div class="w-6 h-6 bg-slate-300 rounded-full absolute left-0 z-20 shadow-lg border-2 border-slate-400 flex items-center justify-center">
                            <div id="ui-led" class="w-2 h-2 rounded-full bg-red-500 neon-glow"></div>
                        </div>
                        <div id="ui-gate-arm" class="h-3 w-48 bg-gradient-to-r from-red-500 via-white to-red-500 rounded-r-full absolute left-3 z-10 gate-pivot gate-closed shadow-2xl"></div>
                    </div>
                    <div class="absolute bottom-4 right-4">
                        <span id="ui-gate-text" class="px-4 py-2 rounded-lg text-xs font-black tracking-widest uppercase bg-red-500/10 text-red-400 border border-red-500/20 backdrop-blur">
                            TERTUTUP
                        </span>
                    </div>
                </div>

                <div class="bento-card p-6 flex-grow">
                    <h4 class="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-chart-area text-blue-400"></i> Trafik Distribusi Kendaraan
                    </h4>
                    <div class="h-[180px] w-full"><canvas id="trafficChart"></canvas></div>
                </div>
            </div>

            <div class="md:col-span-12 lg:col-span-3 flex flex-col gap-6">
                <div class="bento-card p-4 grid grid-cols-2 gap-2">
                    <button onclick="triggerManual()" class="col-span-2 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20">
                        <i class="fa-solid fa-laptop-code"></i> Trigger Sensor Manual
                    </button>
                    <button onclick="Swal.fire('Info', 'Fitur export dimatikan sementara saat integrasi database', 'info')" class="py-3 bg-slate-800 hover:bg-slate-700 text-blue-400 border border-slate-700 rounded-xl text-[10px] font-bold transition flex flex-col items-center justify-center gap-1">
                        <i class="fa-solid fa-file-word text-lg"></i> Unduh .DOC
                    </button>
                    <button onclick="formatDatabase()" class="py-3 bg-slate-800 hover:bg-slate-700 text-red-400 border border-slate-700 rounded-xl text-[10px] font-bold transition flex flex-col items-center justify-center gap-1">
                        <i class="fa-solid fa-trash-can text-lg"></i> Format Data
                    </button>
                </div>
                <div class="bento-card p-5 flex-grow flex flex-col max-h-[340px]">
                    <h4 class="text-sm font-bold text-slate-300 mb-4 pb-2 border-b border-slate-700/50 flex justify-between items-center">
                        <span>Aktivitas Terbaru</span>
                        <span class="text-[10px] bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">Database</span>
                    </h4>
                    <div id="ui-logs-container" class="space-y-2 overflow-y-auto pr-2 flex-grow"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let trafficChartCtx = document.getElementById('trafficChart').getContext('2d');
        let trafficChart;
        let lastLogHtml = ''; 

        function initChart() {
            Chart.defaults.color = '#64748b';
            Chart.defaults.font.family = 'Plus Jakarta Sans';
            let gradient = trafficChartCtx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

            trafficChart = new Chart(trafficChartCtx, {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{ 
                        label: 'Volume', data: [0, 0, 0, 0, 0, 0], borderColor: '#3b82f6', backgroundColor: gradient, 
                        borderWidth: 2, pointBackgroundColor: '#1e293b', pointBorderColor: '#3b82f6',
                        pointBorderWidth: 2, pointRadius: 4, tension: 0.4, fill: true 
                    }]
                },
                options: { 
                    responsive: true, maintainAspectRatio: false, 
                    plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } }, 
                    scales: { 
                        x: { grid: { display: false }, ticks: { font: { size: 10 } } }, 
                        y: { grid: { color: 'rgba(255,255,255,0.05)', borderDash: [5, 5] }, ticks: { font: { size: 10 }, stepSize: 1 }, beginAtZero: true } 
                    } 
                }
            });
        }

        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString('id-ID'); }, 1000);

        function triggerManual() { fetch('/api/trigger', { method: 'POST' }).then(() => loadDashboardData()); }

        function formatDatabase() {
            Swal.fire({
                title: 'Format Database?', text: "Semua data di Supabase akan dihapus permanen.", icon: 'warning',
                showCancelButton: true, confirmButtonColor: '#ef4444', cancelButtonColor: '#334155',
                confirmButtonText: 'Format', background: '#1e293b', color: '#f8fafc'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch('/api/format', { method: 'POST' }).then(() => loadDashboardData());
                }
            });
        }

        function deleteLog(id) { fetch(`/api/log/delete/${id}`, { method: 'DELETE' }).then(() => loadDashboardData()); }

        function loadDashboardData() {
            fetch('/api/stats').then(res => res.json()).then(data => {
                document.getElementById('ui-total').innerText = data.total;
                
                let distBadge = document.getElementById('ui-dist-badge');
                let distText = document.getElementById('ui-distance');
                let distUnit = document.getElementById('ui-dist-unit');
                
                if (data.distance === 999) {
                    distText.innerText = "Aman";
                    distText.classList.replace("text-indigo-400", "text-emerald-400");
                    distUnit.style.opacity = '0'; 
                    distBadge.innerText = "STANDBY"; 
                    distBadge.className = "text-[10px] px-2 py-1 rounded bg-slate-800 text-slate-400 font-bold";
                    document.getElementById('ui-dist-bar').style.width = '0%';
                } else {
                    distText.innerText = data.distance;
                    distText.classList.replace("text-emerald-400", "text-indigo-400");
                    distUnit.style.opacity = '1'; 
                    let distPercent = Math.min((data.distance / 50) * 100, 100); 
                    document.getElementById('ui-dist-bar').style.width = distPercent + '%';
                    
                    if(data.distance > 0 && data.distance <= 10) {
                        distBadge.innerText = "KENDARAAN MASUK"; 
                        distBadge.className = "text-[10px] px-2 py-1 rounded bg-red-500/20 text-red-400 font-bold animate-pulse";
                    } else {
                        distBadge.innerText = "MENDETEKSI"; 
                        distBadge.className = "text-[10px] px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 font-bold";
                    }
                }
                
                const arm = document.getElementById('ui-gate-arm');
                const text = document.getElementById('ui-gate-text');
                const led = document.getElementById('ui-led');
                
                if (data.gate === 'BUKA') {
                    arm.classList.add('gate-open');
                    arm.classList.remove('gate-closed');
                    led.className = "w-2 h-2 rounded-full bg-emerald-500 neon-glow";
                    text.innerText = "PALANG TERBUKA";
                    text.className = "px-4 py-2 rounded-lg text-xs font-black tracking-widest uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur shadow-[0_0_15px_rgba(16,185,129,0.2)]";
                } else {
                    arm.classList.add('gate-closed');
                    arm.classList.remove('gate-open');
                    led.className = "w-2 h-2 rounded-full bg-red-500 neon-glow";
                    text.innerText = "PALANG TERTUTUP";
                    text.className = "px-4 py-2 rounded-lg text-xs font-black tracking-widest uppercase bg-red-500/10 text-red-400 border border-red-500/20 backdrop-blur";
                }

                let logHtml = '';
                if (data.logs.length === 0) {
                    logHtml = '<div class="text-xs text-slate-500 text-center py-8">Belum ada kendaraan yang melintas.</div>';
                } else {
                    data.logs.forEach(log => {
                        let waktuStr = log[1];
                        let waktuSplit = waktuStr.split(' ');
                        let jamFormat = waktuSplit.length > 1 ? waktuSplit[1] : waktuStr;
                        logHtml += `
                            <div class="flex justify-between items-center p-3 bg-slate-800/40 rounded-xl border border-slate-700/50 hover:bg-slate-700/40 transition group">
                                <div class="flex items-center gap-3">
                                    <div class="w-8 h-8 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center text-[10px]">
                                        <i class="fa-solid fa-car"></i>
                                    </div>
                                    <div>
                                        <span class="font-mono font-bold text-slate-200 text-xs">#LOG-${String(log[0]).padStart(4, '0')}</span>
                                        <span class="text-slate-400 block text-[10px] mt-0.5">${jamFormat} WIB</span>
                                    </div>
                                </div>
                                <button onclick="deleteLog(${log[0]})" class="text-slate-600 hover:text-red-400 transition hover:scale-110 p-2 cursor-pointer z-10" title="Hapus Data">
                                    <i class="fa-solid fa-xmark"></i>
                                </button>
                            </div>
                        `;
                    });
                }
                
                if (lastLogHtml !== logHtml) {
                    document.getElementById('ui-logs-container').innerHTML = logHtml;
                    lastLogHtml = logHtml;
                }
            }).catch(e => console.error("Fetch Error:", e));
        }

        initChart();
        setInterval(loadDashboardData, 1500); 
    </script>
</body>
</html>
"""

# === BACKEND API ROUTING ===
@app.route('/')
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/stats')
def api_stats():
    logs_data = []
    total_logs = 0
    jarak_sekarang = 999
    palang_sekarang = "TUTUP"

    if supabase:
        try:
            # 1. Ambil status alat real-time dari tabel status_alat
            status_res = supabase.table('status_alat').select('*').eq('id', 1).execute()
            if status_res.data:
                jarak_sekarang = status_res.data[0]['jarak']
                palang_sekarang = status_res.data[0]['palang']

            # 2. Ambil 10 logs terbaru
            response = supabase.table('log_kendaraan').select('*').order('id', desc=True).limit(10).execute()
            for row in response.data:
                raw_waktu = str(row['waktu_masuk']).replace('T', ' ').split('+')[0].split('.')[0]
                logs_data.append([row['id'], raw_waktu])
            
            # 3. Hitung total logs
            count_response = supabase.table('log_kendaraan').select('*', count='exact').execute()
            total_logs = count_response.count if count_response.count else 0
        except Exception as e:
            print(f"Error DB Fetch: {e}")

    return jsonify({
        'total': total_logs,
        'logs': logs_data,
        'gate': palang_sekarang,
        'distance': jarak_sekarang,
        'chart_data': {'labels': ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'], 'values': [0,0,0,0,0,0]}
    })

@app.route('/api/update_sensor', methods=['POST'])
def api_update_sensor():
    data = request.json
    if not supabase: return jsonify({'status': 'error', 'msg': 'No DB'})

    try:
        update_data = {}
        if 'distance' in data: 
            update_data['jarak'] = data['distance']
        if 'gate' in data: 
            update_data['palang'] = data['gate']
            
        if update_data:
            supabase.table('status_alat').update(update_data).eq('id', 1).execute()
            
        if data.get('trigger_log') == True:
            waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            supabase.table('log_kendaraan').insert({'waktu_masuk': waktu_sekarang}).execute()
    except Exception as e:
        print(f"Error Update Sensor: {e}")
        
    return jsonify({'status': 'ok'})

@app.route('/api/trigger', methods=['POST'])
def api_trigger():
    if supabase:
        try:
            waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            supabase.table('log_kendaraan').insert({'waktu_masuk': waktu_sekarang}).execute()
            supabase.table('status_alat').update({'palang': 'BUKA'}).eq('id', 1).execute()
        except Exception as e:
            print(f"Error Manual Trigger: {e}")
    
    def tutup_palang_otomatis():
        time.sleep(2)
        if supabase:
            supabase.table('status_alat').update({'palang': 'TUTUP'}).eq('id', 1).execute()
            
    threading.Thread(target=tutup_palang_otomatis).start()
    return jsonify({'status': 'ok'})

@app.route('/api/log/delete/<int:log_id>', methods=['DELETE'])
def api_delete_log(log_id):
    if supabase:
        supabase.table('log_kendaraan').delete().eq('id', log_id).execute()
    return jsonify({'status': 'ok'})

@app.route('/api/format', methods=['POST'])
def api_format():
    if supabase:
        supabase.table('log_kendaraan').delete().gt('id', 0).execute()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run()