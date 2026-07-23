from flask import Flask, render_template_string, request, jsonify
import json

app = Flask(__name__)

# Template HTML Dashboard dengan Tailwind CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Blasting Filtered</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 min-h-screen p-8">
    <div class="max-w-5xl mx-auto space-y-6">
        
        <!-- Header -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h1 class="text-2xl font-bold text-slate-800">🚀 Dashboard Blasting Target</h1>
            <p class="text-slate-500 text-sm mt-1">Kirim pesan terpersonalisasi berdasarkan filter kriteria tiap penerima.</p>
        </div>

        <!-- Form Blasting -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 class="text-lg font-semibold text-slate-700 mb-4">1. Buat Kampanye Blasting</h2>
            <form id="blastingForm" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-600 mb-1">Pilih Target Berdasarkan Filter Region:</label>
                    <select id="filterRegion" class="w-full p-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none">
                        <option value="ALL">Semua Region</option>
                        <option value="Jakarta">Jakarta</option>
                        <option value="Bandung">Bandung</option>
                        <option value="Surabaya">Surabaya</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-600 mb-1">Filter Kategori Penerima:</label>
                    <select id="filterKategori" class="w-full p-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none">
                        <option value="ALL">Semua Kategori</option>
                        <option value="VIP">VIP</option>
                        <option value="Regular">Regular</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-600 mb-1">Template Pesan (Gunakan {nama} untuk variabel dinamis):</label>
                    <textarea id="pesanTemplate" rows="3" class="w-full p-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Halo {nama}, ada penawaran khusus untuk Anda!"></textarea>
                </div>

                <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg transition-all shadow-sm">
                    Jalankan Blasting
                </button>
            </form>
        </div>

        <!-- Status Hasil Blasting -->
        <div id="resultCard" class="hidden bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 class="text-lg font-semibold text-slate-700 mb-3">2. Laporan Hasil Pengiriman</h2>
            <div id="summaryText" class="text-sm font-medium text-slate-600 mb-4"></div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-600">
                    <thead class="text-xs uppercase bg-slate-50 text-slate-700 border-b">
                        <tr>
                            <th class="py-3 px-4">Nama</th>
                            <th class="py-3 px-4">Region</th>
                            <th class="py-3 px-4">Kategori</th>
                            <th class="py-3 px-4">Pesan Terkirim</th>
                            <th class="py-3 px-4">Status</th>
                        </tr>
                    </thead>
                    <tbody id="resultTable" class="divide-y divide-slate-100"></tbody>
                </table>
            </div>
        </div>

    </div>

    <script>
        document.getElementById('blastingForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const payload = {
                region: document.getElementById('filterRegion').value,
                kategori: document.getElementById('filterKategori').value,
                pesan: document.getElementById('pesanTemplate').value
            };

            const response = await fetch('/api/blast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            
            // Render Hasil
            document.getElementById('resultCard').classList.remove('hidden');
            document.getElementById('summaryText').innerText = `Total Target Terfilter: ${data.total_sent} Penerima`;

            const tbody = document.getElementById('resultTable');
            tbody.innerHTML = '';
            data.details.forEach(item => {
                tbody.innerHTML += `
                    <tr class="hover:bg-slate-50">
                        <td class="py-3 px-4 font-medium text-slate-800">${item.nama}</td>
                        <td class="py-3 px-4">${item.region}</td>
                        <td class="py-3 px-4"><span class="px-2 py-1 text-xs rounded-md ${item.kategori === 'VIP' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}">${item.kategori}</span></td>
                        <td class="py-3 px-4 italic text-slate-500">${item.pesan_terkirim}</td>
                        <td class="py-3 px-4"><span class="text-emerald-600 font-semibold">✓ ${item.status}</span></td>
                    </tr>
                `;
            });
        });
    </script>
</body>
</html>
"""

# Dummy Database Penerima dengan atribut filter masing-masing
DATABASE_PENERIMA = [
    {"id": 1, "nama": "Andi Pratama", "region": "Jakarta", "kategori": "VIP", "kontak": "08123456789"},
    {"id": 2, "nama": "Budi Santoso", "region": "Bandung", "kategori": "Regular", "kontak": "08234567890"},
    {"id": 3, "nama": "Citra Lestari", "region": "Jakarta", "kategori": "Regular", "kontak": "08345678901"},
    {"id": 4, "nama": "Dewi Rahma", "region": "Surabaya", "kategori": "VIP", "kontak": "08456789012"},
    {"id": 5, "nama": "Eko Wijaya", "region": "Bandung", "kategori": "VIP", "kontak": "08567890123"}
]

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/blast', methods=['POST'])
def send_blast():
    data = request.json
    filter_region = data.get('region', 'ALL')
    filter_kategori = data.get('kategori', 'ALL')
    pesan_template = data.get('pesan', '')

    # Filter Penerima berdasarkan Kriteria
    target_penerima = []
    for p in DATABASE_PENERIMA:
        match_region = (filter_region == 'ALL' or p['region'] == filter_region)
        match_kategori = (filter_kategori == 'ALL' or p['kategori'] == filter_kategori)

        if match_region and match_kategori:
            # Personalisasi pesan per penerima
            pesan_personal = pesan_template.replace("{nama}", p['nama'])
            
            # (Di sini tempat Anda menambahkan logika integrasi WhatsApp API / Email Provider)
            
            target_penerima.append({
                "nama": p['nama'],
                "region": p['region'],
                "kategori": p['kategori'],
                "pesan_terkirim": pesan_personal,
                "status": "Success"
            })

    return jsonify({
        "status": "completed",
        "total_sent": len(target_penerima),
        "details": target_penerima
    })

# Handler khusus Vercel Serverless
def handler(request, start_response):
    return app(request, start_response)

if __name__ == '__main__':
    app.run(debug=True)