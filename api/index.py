import json
import datetime
import os
import io
import csv
from flask import Flask, render_template_string, request, jsonify
import uuid
import requests as req_lib

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Blasting Target</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .fade-in { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .loader { border-top-color: #2563eb; -webkit-animation: spinner 1.5s linear infinite; animation: spinner 1.5s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-slate-100 min-h-screen">
    <nav class="bg-white border-b border-slate-200 px-6 py-4">
        <div class="max-w-6xl mx-auto flex items-center justify-between">
            <h1 class="text-xl font-bold text-slate-800">Dashboard Blasting Target</h1>
            <div class="flex gap-2">
                <button onclick="showTab('dashboard')" id="tab-dashboard" class="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white transition">Dashboard</button>
                <button onclick="showTab('recipients')" id="tab-recipients" class="px-4 py-2 rounded-lg text-sm font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Penerima</button>
                <button onclick="showTab('settings')" id="tab-settings" class="px-4 py-2 rounded-lg text-sm font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Pengaturan</button>
            </div>
        </div>
    </nav>

    <div class="max-w-6xl mx-auto p-6 space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Total Penerima</p>
                <p class="text-2xl font-bold text-slate-800 mt-1" id="stat-total">5</p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">High Potential</p>
                <p class="text-2xl font-bold text-red-600 mt-1" id="stat-high">0</p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Medium Potential</p>
                <p class="text-2xl font-bold text-amber-600 mt-1" id="stat-medium">0</p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Low Potential</p>
                <p class="text-2xl font-bold text-slate-600 mt-1" id="stat-low">0</p>
            </div>
            <div class="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
                <p class="text-xs font-medium text-slate-500 uppercase">Pesan Terkirim</p>
                <p class="text-2xl font-bold text-emerald-600 mt-1" id="stat-sent">0</p>
            </div>
        </div>

        <div id="tab-dashboard-content" class="space-y-6">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h2 class="text-lg font-semibold text-slate-700 mb-4">Buat Kampanye Blasting</h2>
                <form id="blastingForm" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-slate-600 mb-1">Filter Kategori</label>
                            <select id="filterKategori" class="w-full p-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none">
                                <option value="ALL">Semua Kategori</option>
                                <option value="High Potential">High Potential</option>
                                <option value="Medium Potential">Medium Potential</option>
                                <option value="Low Potential">Low Potential</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-600 mb-1">Template Pesan <span class="text-slate-400 text-xs">({nama}, {kategori}, {kontak}, {sme_opportunity_score})</span></label>
                        <textarea id="pesanTemplate" rows="3" class="w-full p-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm" placeholder="Halo {nama}, ada penawaran khusus untuk Anda!">Halo {nama}, berdasarkan analisis kami Anda termasuk kategori {kategori} dengan skor SME opportunity {sme_opportunity_score}. Hubungi kami di {kontak} untuk info lebih lanjut.</textarea>
                    </div>
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <label class="block text-sm font-medium text-slate-600">Pilih Penerima</label>
                            <button type="button" onclick="toggleAllRecipients()" class="text-xs text-blue-600 hover:text-blue-700 font-medium">Pilih Semua</button>
                        </div>
                        <div id="recipientPicker" class="border border-slate-200 rounded-lg p-3 max-h-56 overflow-y-auto bg-slate-50">
                            <p class="text-sm text-slate-400">Muat penerima...</p>
                        </div>
                        <p class="text-xs text-slate-400 mt-1">Gunakan filter di atas untuk menyaring daftar, lalu pilih penerima yang diinginkan.</p>
                    </div>
                    <div class="flex items-center gap-3">
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg transition-all shadow-sm">
                            Jalankan Blasting
                        </button>
                        <span id="sendStatus" class="text-sm text-slate-500 hidden"></span>
                    </div>
                    <p id="providerHint" class="text-xs text-amber-600 hidden">Mode Mock aktif: pesan hanya disimulasikan. Aktifkan provider di tab Pengaturan untuk mengirim pesan nyata.</p>
                </form>
            </div>

            <div id="resultCard" class="hidden bg-white p-6 rounded-xl shadow-sm border border-slate-200 fade-in">
                <h2 class="text-lg font-semibold text-slate-700 mb-3">Laporan Hasil Pengiriman</h2>
                <div id="summaryText" class="text-sm font-medium text-slate-600 mb-4"></div>
                <div class="mb-3">
                    <button onclick="updateRecipientsFromBlast()" class="text-sm text-emerald-600 hover:text-emerald-700 font-medium">Update data nasabah dari hasil blast ini</button>
                </div>
                <div id="resultArea"></div>
            </div>
        </div>

        <div id="tab-recipients-content" class="hidden space-y-6">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h2 class="text-lg font-semibold text-slate-700 mb-4">Tambah Penerima Manual</h2>
                <form id="addRecipientForm" class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <input type="text" id="nama" required placeholder="Nama Nasabah" class="p-2.5 border rounded-lg border-slate-300 text-sm">
                    <input type="text" id="kontak" required placeholder="Nomor WhatsApp" class="p-2.5 border rounded-lg border-slate-300 text-sm">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-4 py-2 rounded-lg text-sm transition">Tambah</button>
                </form>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h2 class="text-lg font-semibold text-slate-700 mb-4">Import CSV</h2>
                <div class="flex items-center gap-4">
                    <input type="file" id="csvFile" accept=".csv" class="text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                    <button onclick="uploadCSV()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm transition">Import</button>
                </div>
                <p class="text-xs text-slate-400 mt-2">Format CSV: nama, kontak, kategori, end_balance, giro, deposito, dpk, sme_opportunity_score (header harus sesuai)</p>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-lg font-semibold text-slate-700">Daftar Penerima</h2>
                    <div class="flex gap-2">
                        <button onclick="refreshRecipients()" class="text-sm text-blue-600 hover:text-blue-700 font-medium">Refresh</button>
                        <button onclick="updateDataCSV()" class="text-sm text-emerald-600 hover:text-emerald-700 font-medium">Update Data CSV (Replace All)</button>
                        <button onclick="syncFromGoogleSheet()" class="text-sm text-purple-600 hover:text-purple-700 font-medium">Sync from Google Sheet</button>
                    </div>
                </div>
                <input type="file" id="csvUpdateFile" accept=".csv" class="text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-3">
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left text-slate-600">
                        <thead class="text-xs uppercase bg-slate-50 text-slate-700 border-b">
                            <tr>
                                <th class="py-3 px-4">Nama Nasabah</th>
                                <th class="py-3 px-4">Kategori</th>
                                <th class="py-3 px-4">Nomor WhatsApp</th>
                                <th class="py-3 px-4">SME Score</th>
                                <th class="py-3 px-4">Aksi</th>
                            </tr>
                        </thead>
                        <tbody id="recipientTable" class="divide-y divide-slate-100"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="tab-settings-content" class="hidden space-y-6">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h2 class="text-lg font-semibold text-slate-700 mb-4">Pengaturan WhatsApp API</h2>
                <div class="space-y-4 max-w-2xl">
                    <div>
                        <label class="block text-sm font-medium text-slate-600 mb-1">Provider</label>
                        <select id="waProvider" onchange="updateProviderFields()" class="w-full p-2.5 border rounded-lg border-slate-300 text-sm">
                            <option value="mock">Mock (Testing)</option>
                            <option value="wablas">Wablas</option>
                            <option value="fonnte">Fonnte</option>
                            <option value="twilio">Twilio</option>
                            <option value="meta">Meta WhatsApp Business API</option>
                        </select>
                    </div>
                    <div id="apiKeyField">
                        <label class="block text-sm font-medium text-slate-600 mb-1">API Key / Token</label>
                        <input type="password" id="apiKey" class="w-full p-2.5 border rounded-lg border-slate-300 text-sm" placeholder="Masukkan API key Anda">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-600 mb-1">Sender Number (opsional)</label>
                        <input type="text" id="senderNumber" class="w-full p-2.5 border rounded-lg border-slate-300 text-sm" placeholder="628123456789">
                    </div>
                    <button onclick="saveSettings()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition">Simpan Pengaturan</button>
                    <span id="settingsStatus" class="text-sm text-emerald-600 hidden ml-4">Tersimpan!</span>
                </div>
                <div class="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
                    <p class="font-medium">Catatan untuk Vercel:</p>
                    <p>Untuk deployment di Vercel, set environment variables di dashboard Vercel:</p>
                    <ul class="list-disc ml-5 mt-1 space-y-1">
                        <li><code class="bg-blue-100 px-1 rounded">WHATSAPP_PROVIDER</code> (mock, wablas, fonnte, twilio, meta)</li>
                        <li><code class="bg-blue-100 px-1 rounded">WHATSAPP_API_KEY</code></li>
                        <li><code class="bg-blue-100 px-1 rounded">WHATSAPP_SENDER_NUMBER</code></li>
                    </ul>
                    <p class="mt-2">Settings yang disimpan di ui tidak persisten di Vercel, jadi pakai environment variables untuk production.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showTab(tab) {
            ['dashboard', 'recipients', 'settings'].forEach(t => {
                const btn = document.getElementById('tab-'+t);
                btn.className = t === tab ? 'px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white transition' : 'px-4 py-2 rounded-lg text-sm font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition';
                document.getElementById('tab-'+t+'-content').classList.add('hidden');
            });
            document.getElementById('tab-'+tab+'-content').classList.remove('hidden');
        }

        async function loadRecipients() {
            const res = await fetch('/api/recipients');
            const data = await res.json();
            const recipients = data.recipients || [];
            const tbody = document.getElementById('recipientTable');
            if (!recipients.length) { tbody.innerHTML = '<tr><td colspan="5" class="py-4 text-center text-slate-400">Belum ada penerima.</td></tr>'; }
            else {
                tbody.innerHTML = recipients.map(r => {
                    const badgeClass = r.kategori === 'High Potential' ? 'bg-red-100 text-red-700' : r.kategori === 'Medium Potential' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600';
                    return `<tr class="hover:bg-slate-50">
                        <td class="py-3 px-4 font-medium text-slate-800">${escapeHtml(r.nama)}</td>
                        <td class="py-3 px-4"><span class="px-2 py-1 text-xs rounded-md ${badgeClass}">${escapeHtml(r.kategori)}</span></td>
                        <td class="py-3 px-4">${escapeHtml(r.kontak)}</td>
                        <td class="py-3 px-4 text-xs">${escapeHtml(r.sme_opportunity_score || '')}</td>
                        <td class="py-3 px-4"><button onclick="deleteRecipient('${r.id}')" class="text-red-600 hover:text-red-700 text-xs font-medium">Hapus</button></td>
                    </tr>`;
                }).join('');
            }
            document.getElementById('stat-total').textContent = recipients.length;
            document.getElementById('stat-high').textContent = recipients.filter(r => r.kategori === 'High Potential').length;
            document.getElementById('stat-medium').textContent = recipients.filter(r => r.kategori === 'Medium Potential').length;
            document.getElementById('stat-low').textContent = recipients.filter(r => r.kategori === 'Low Potential').length;
            await loadRecipientPicker();
        }

        async function loadRecipientPicker() {
            const kategori = document.getElementById('filterKategori').value;
            const res = await fetch('/api/recipients');
            const data = await res.json();
            let recipients = data.recipients || [];
            if (kategori !== 'ALL') recipients = recipients.filter(r => r.kategori === kategori);
            const container = document.getElementById('recipientPicker');
            if (!recipients.length) { container.innerHTML = '<p class="text-sm text-slate-400">Tidak ada penerima untuk filter ini.</p>'; return; }
            container.innerHTML = recipients.map(r => {
                const badgeClass = r.kategori === 'High Potential' ? 'bg-red-100 text-red-700' : r.kategori === 'Medium Potential' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600';
                return `<label class="flex items-center justify-between gap-2 p-2 hover:bg-white rounded cursor-pointer">
                    <div class="flex items-center gap-2">
                        <input type="checkbox" value="${r.id}" class="recipient-checkbox rounded border-slate-300 text-blue-600 focus:ring-blue-500">
                        <div>
                            <span class="text-sm text-slate-700 font-medium">${escapeHtml(r.nama)}</span>
                            <span class="text-xs text-slate-400 ml-1">${escapeHtml(r.kontak)}</span>
                        </div>
                    </div>
                    <span class="px-2 py-1 text-xs rounded-md ${badgeClass}">${escapeHtml(r.kategori)}</span>
                </label>`;
            }).join('');
        }

        function toggleAllRecipients() {
            const checkboxes = document.querySelectorAll('.recipient-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        }

        document.getElementById('filterKategori').addEventListener('change', loadRecipientPicker);

        document.getElementById('blastingForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const selected = Array.from(document.querySelectorAll('.recipient-checkbox:checked')).map(cb => cb.value);
            console.log('Selected recipients:', selected);
            if (!selected.length) { alert('Pilih minimal satu penerima.'); return; }
            const payload = {
                recipient_ids: selected,
                pesan: document.getElementById('pesanTemplate').value
            };
            const statusEl = document.getElementById('sendStatus');
            statusEl.classList.remove('hidden');
            statusEl.innerHTML = '<div class="loader ease-linear rounded-full border-2 border-t-2 border-gray-200 h-4 w-4 inline-block"></div> Mengirim...';
            let res;
            try {
                res = await fetch('/api/blast', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            } catch (err) {
                statusEl.classList.add('hidden');
                alert('Network error: ' + err.message);
                console.error('Fetch error:', err);
                return;
            }
            statusEl.classList.add('hidden');
            let data;
            try {
                data = await res.json();
            } catch (err) {
                alert('Gagal parsing response. HTTP status: ' + res.status);
                console.error('JSON parse error:', err, await res.text());
                return;
            }
            console.log('Blast response:', data);
            if (data.status !== 'ok') { alert(data.error || 'Gagal'); return; }
            await loadHistory();
            document.getElementById('resultCard').classList.remove('hidden');
            document.getElementById('summaryText').textContent = `Total Target Terkirim: ${data.total_sent} Penerima | Provider: ${data.provider || 'mock'}`;
            const area = document.getElementById('resultArea');
            const failedCount = (data.details || []).filter(item => item.status === 'Failed').length;
            const mockCount = (data.details || []).filter(item => item.status === 'Mock').length;
            let summary = data.details ? `${data.total_sent} target, ${failedCount} gagal` : '0 target';
            if (mockCount) summary += ` (${mockCount} mock, belum benar-benar terkirim)`;
            if (data.provider === 'mock' && data.total_sent > 0) summary += ' | Mode Mock aktif';
            document.getElementById('summaryText').textContent = summary;
            area.innerHTML = '<div class="overflow-x-auto"><table class="w-full text-sm text-left text-slate-600"><thead class="text-xs uppercase bg-slate-50 text-slate-700 border-b"><tr><th class="py-3 px-4">Nama</th><th class="py-3 px-4">Kategori</th><th class="py-3 px-4">Kontak</th><th class="py-3 px-4">Pesan Terkirim</th><th class="py-3 px-4">Status</th><th class="py-3 px-4">Info</th></tr></thead><tbody class="divide-y divide-slate-100">' + (data.details || []).map(item => {
                const badgeClass = item.kategori === 'High Potential' ? 'bg-red-100 text-red-700' : item.kategori === 'Medium Potential' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600';
                const statusClass = item.status === 'Sent' ? 'text-emerald-600' : item.status === 'Mock' ? 'text-amber-600' : 'text-red-600';
                const infoText = item.error || item.provider || '';
                return `<tr class="hover:bg-slate-50"><td class="py-3 px-4 font-medium text-slate-800">${escapeHtml(item.nama)}</td><td class="py-3 px-4"><span class="px-2 py-1 text-xs rounded-md ${badgeClass}">${escapeHtml(item.kategori)}</span></td><td class="py-3 px-4">${escapeHtml(item.kontak)}</td><td class="py-3 px-4 italic text-slate-500">${escapeHtml(item.pesan_terkirim)}</td><td class="py-3 px-4"><span class="${statusClass} font-semibold">${escapeHtml(item.status)}</span></td><td class="py-3 px-4 text-xs">${escapeHtml(infoText)}</td></tr>`;
            }).join('') + '</tbody></table></div>';
        });

        async function updateDataCSV() {
            const fileInput = document.getElementById('csvUpdateFile');
            if (!fileInput.files.length) { alert('Pilih file CSV untuk update data terlebih dahulu.'); return; }
            if (!confirm('Ini akan mengganti SEMUA data nasabah dengan data dari file ini. Lanjutkan?')) return;
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            const res = await fetch('/api/recipients/replace', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'ok') { alert(`Data berhasil diupdate: ${data.total} penerima.`); fileInput.value = ''; await loadRecipients(); await loadRecipientPicker(); }
            else { alert('Gagal update: ' + (data.error || 'Unknown')); }
        }

        async function updateRecipientsFromBlast() {
            if (!confirm('Update data nasabah dari hasil blast terakhir?')) return;
            const res = await fetch('/api/history');
            const data = await res.json();
            const history = data.history || [];
            if (!history.length) { alert('Belum ada history blast.'); return; }
            const last = history[history.length - 1];
            const payload = { recipients: last.details || [] };
            const updateRes = await fetch('/api/recipients/replace', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const updateData = await updateRes.json();
            if (updateData.status === 'ok') { alert(`Data berhasil diupdate: ${updateData.total} penerima.`); await loadRecipients(); await loadRecipientPicker(); }
            else { alert('Gagal update: ' + (updateData.error || 'Unknown')); }
        }

        async function uploadCSV() {
            const fileInput = document.getElementById('csvFile');
            if (!fileInput.files.length) { alert('Pilih file CSV terlebih dahulu.'); return; }
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            const res = await fetch('/api/recipients/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'ok') { alert(`Import berhasil: ${data.added} data.`); fileInput.value = ''; await loadRecipients(); }
            else { alert('Gagal import: ' + (data.error || 'Unknown')); }
        }

        async function deleteRecipient(id) {
            if (!confirm('Hapus penerima ini?')) return;
            await fetch('/api/recipients/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
            await loadRecipients();
        }

        document.getElementById('addRecipientForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const nama = document.getElementById('nama').value.trim();
            const kontak = document.getElementById('kontak').value.trim();
            if (!nama || !kontak) { alert('Nama dan Nomor WhatsApp wajib diisi.'); return; }
            if (!/^\+?\d{10,15}$/.test(kontak.replace(/\s/g, ''))) { alert('Format nomor WhatsApp tidak valid. Contoh: 6281234567890'); return; }
            const payload = { nama, kontak };
            const res = await fetch('/api/recipients/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (res.ok) { document.getElementById('addRecipientForm').reset(); await loadRecipients(); await loadRecipientPicker(); alert('Penerima berhasil ditambahkan.'); }
            else { alert('Gagal menambah penerima.'); }
        });

        async function syncFromGoogleSheet() {
            if (!confirm('Sync data dari Google Sheet? Data lama akan diganti.')) return;
            const statusEl = document.getElementById('sendStatus');
            statusEl.classList.remove('hidden');
            statusEl.innerHTML = 'Mengambil data dari Google Sheet...';
            try {
                const res = await fetch('/api/recipients/sync-sheets', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'ok') { alert(`Sync berhasil: ${data.total} penerima.`); await loadRecipients(); await loadRecipientPicker(); }
                else { alert('Gagal sync: ' + (data.error || 'Unknown')); }
            } catch (err) {
                alert('Network error: ' + err.message);
            } finally {
                statusEl.classList.add('hidden');
            }
        }

        async function loadSettings() {
            const res = await fetch('/api/settings');
            const data = await res.json();
            const currentSettings = data.settings || {};
            document.getElementById('waProvider').value = currentSettings.provider || 'mock';
            document.getElementById('apiKey').value = currentSettings.apiKey || '';
            document.getElementById('senderNumber').value = currentSettings.senderNumber || '';
            updateProviderFields();
        }

        async function saveSettings() {
            const payload = {
                provider: document.getElementById('waProvider').value,
                apiKey: document.getElementById('apiKey').value,
                senderNumber: document.getElementById('senderNumber').value
            };
            await fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ settings: payload }) });
            const el = document.getElementById('settingsStatus');
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 2000);
        }

        function updateProviderFields() {
            const provider = document.getElementById('waProvider').value;
            const label = document.querySelector('#apiKeyField label');
            if (provider === 'mock') { label.textContent = 'API Key / Token (tidak diperlukan)'; }
            else { label.textContent = 'API Key / Token'; }
            const hint = document.getElementById('providerHint');
            if (hint) { hint.classList.toggle('hidden', provider !== 'mock'); }
        }

        async function checkProviderMode() {
            const res = await fetch('/api/settings');
            const data = await res.json();
            const provider = (data.settings || {}).provider || 'mock';
            const hint = document.getElementById('providerHint');
            if (hint) { hint.classList.toggle('hidden', provider !== 'mock'); }
        }

        (function init() { loadRecipients(); loadHistory(); loadSettings(); loadRecipientPicker(); })();
    </script>
</body>
</html>
"""

DATABASE_PENERIMA = [
    {"id": "1", "nama": "ADA SEKATA BERSAMA", "kontak": "08123456789", "kategori": "Low Potential", "end_balance": "812,977", "giro": "0", "deposito": "0", "dpk": "812,977", "mutasi_debit_apr": "0", "mutasi_debit_mei": "0", "mutasi_debit_jun": "0", "mutasi_kredit_apr": "0", "mutasi_kredit_mei": "0", "mutasi_kredit_jun": "0", "avg_mutasi_debit": "0", "avg_mutasi_kredit": "0", "product_score": "5", "balance_score": "0", "debit_score": "0", "kredit_score": "0", "sme_opportunity_score": "5"},
    {"id": "2", "nama": "ASHOKA TEKNIK MARINE", "kontak": "08234567890", "kategori": "Low Potential", "end_balance": "132,932", "giro": "0", "deposito": "0", "dpk": "132,932", "mutasi_debit_apr": "0", "mutasi_debit_mei": "0", "mutasi_debit_jun": "999,990,000", "mutasi_kredit_apr": "0", "mutasi_kredit_mei": "0", "mutasi_kredit_jun": "1,000,000,000", "avg_mutasi_debit": "333,330,000", "avg_mutasi_kredit": "333,333,333", "product_score": "5", "balance_score": "0", "debit_score": "6", "kredit_score": "5", "sme_opportunity_score": "16"},
    {"id": "3", "nama": "BIO PACK SOLUTION", "kontak": "08345678901", "kategori": "Medium Potential", "end_balance": "860,231,528", "giro": "0", "deposito": "0", "dpk": "860,231,528", "mutasi_debit_apr": "610,407,900", "mutasi_debit_mei": "1,817,443,700", "mutasi_debit_jun": "70,005,000", "mutasi_kredit_apr": "814,105,000", "mutasi_kredit_mei": "1,648,141,500", "mutasi_kredit_jun": "873,551,400", "avg_mutasi_debit": "832,618,867", "avg_mutasi_kredit": "1,111,932,633", "product_score": "5", "balance_score": "18", "debit_score": "12", "kredit_score": "15", "sme_opportunity_score": "50"}
]

CAMPAIGN_HISTORY = []

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')


def load_settings_file():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"provider": "mock", "apiKey": "", "senderNumber": ""}


def save_settings_file(data):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_settings():
    settings = load_settings_file()
    env_provider = os.environ.get('WHATSAPP_PROVIDER')
    env_api_key = os.environ.get('WHATSAPP_API_KEY')
    env_sender_number = os.environ.get('WHATSAPP_SENDER_NUMBER')
    if env_provider:
        settings['provider'] = env_provider
    if env_api_key:
        settings['apiKey'] = env_api_key
    if env_sender_number:
        settings['senderNumber'] = env_sender_number
    return settings


def build_wa_payload(provider, text, to, api_key, sender_number):
    provider = (provider or 'mock').lower()
    to = to.replace('+', '').replace(' ', '')
    if provider == 'wablas':
        return {"url": "https://wablas.com/api/send-message", "method": "POST", "headers": {"Authorization": api_key, "Content-Type": "application/json"}, "body": {"phone": to, "message": text, "isGroup": False}}
    if provider == 'fonnte':
        return {"url": "https://api.fonnte.com/send", "method": "POST", "headers": {"Authorization": api_key}, "data": {"target": to, "message": text}}
    if provider == 'twilio':
        return {"url": f"https://api.twilio.com/2010-04-01/Accounts/{sender_number}/Messages.json", "method": "POST", "headers": {"Authorization": "Basic " + api_key}, "body": {"To": f"whatsapp:+{to}", "From": f"whatsapp:+{sender_number}", "Body": text}}
    if provider == 'meta':
        return {"url": f"https://graph.facebook.com/v18.0/{sender_number}/messages", "method": "POST", "headers": {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, "body": {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}}
    return {"mock": True, "text": text, "to": to}


def send_message_via_provider(provider, text, to, api_key, sender_number):
    payload = build_wa_payload(provider, text, to, api_key, sender_number)
    if payload.get("mock"):
        return {"status": "sent", "provider": "mock"}
    try:
        if payload.get("headers", {}).get("Authorization", "").startswith("Basic"):
            import base64
            creds = base64.b64decode(payload["headers"]["Authorization"].replace("Basic ", "")).decode()
            req_lib.request(payload.get("method", "POST"), payload["url"], data=payload.get("body", {}), auth=creds.split(":"), headers=payload.get("headers", {}), timeout=15)
        elif payload.get("headers", {}).get("Authorization", "").startswith("Bearer"):
            req_lib.request(payload.get("method", "POST"), payload["url"], json=payload.get("body", {}), headers=payload.get("headers", {}), timeout=15)
        else:
            req_lib.request(payload.get("method", "POST"), payload["url"], json=payload.get("body", {}), headers=payload.get("headers", {}), timeout=15)
        return {"status": "sent", "provider": provider}
    except Exception as e:
        return {"status": "failed", "provider": provider, "error": str(e)}


@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/recipients')
def get_recipients():
    return jsonify({"recipients": DATABASE_PENERIMA})


@app.route('/api/recipients/add', methods=['POST'])
def add_recipient():
    data = request.json or {}
    new_item = {
        "id": str(uuid.uuid4()),
        "nama": data.get('nama', ''),
        "kontak": data.get('kontak', ''),
        "kategori": data.get('kategori', 'Low Potential'),
        "end_balance": data.get('end_balance', ''),
        "giro": data.get('giro', ''),
        "deposito": data.get('deposito', ''),
        "dpk": data.get('dpk', ''),
        "mutasi_debit_apr": data.get('mutasi_debit_apr', ''),
        "mutasi_debit_mei": data.get('mutasi_debit_mei', ''),
        "mutasi_debit_jun": data.get('mutasi_debit_jun', ''),
        "mutasi_kredit_apr": data.get('mutasi_kredit_apr', ''),
        "mutasi_kredit_mei": data.get('mutasi_kredit_mei', ''),
        "mutasi_kredit_jun": data.get('mutasi_kredit_jun', ''),
        "avg_mutasi_debit": data.get('avg_mutasi_debit', ''),
        "avg_mutasi_kredit": data.get('avg_mutasi_kredit', ''),
        "product_score": data.get('product_score', ''),
        "balance_score": data.get('balance_score', ''),
        "debit_score": data.get('debit_score', ''),
        "kredit_score": data.get('kredit_score', ''),
        "sme_opportunity_score": data.get('sme_opportunity_score', ''),
        "link_chat_1": data.get('link_chat_1', ''),
        "jawaban": data.get('jawaban', ''),
        "link_chat_2": data.get('link_chat_2', '')
    }
    if not new_item['nama'] or not new_item['kontak']:
        return jsonify({"status": "error", "error": "Nama dan kontak wajib diisi"}), 400
    DATABASE_PENERIMA.append(new_item)
    return jsonify({"status": "ok"})


@app.route('/api/recipients/delete', methods=['POST'])
def delete_recipient():
    data = request.json or {}
    rid = data.get('id')
    global DATABASE_PENERIMA
    DATABASE_PENERIMA = [p for p in DATABASE_PENERIMA if p['id'] != rid]
    return jsonify({"status": "ok"})


@app.route('/api/recipients/upload', methods=['POST'])
def upload_recipients():
    file = request.files.get('file')
    if not file:
        return jsonify({"status": "error", "error": "File tidak ditemukan"}), 400
    try:
        import csv, io
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        added = 0
        for row in reader:
            if row.get('nama') and row.get('kontak'):
                DATABASE_PENERIMA.append({
                    "id": str(uuid.uuid4()),
                    "nama": row.get('nama', '').strip(),
                    "kontak": row.get('kontak', '').strip(),
                    "kategori": row.get('kategori', 'Low Potential').strip(),
                    "end_balance": row.get('end_balance', '').strip(),
                    "giro": row.get('giro', '').strip(),
                    "deposito": row.get('deposito', '').strip(),
                    "dpk": row.get('dpk', '').strip(),
                    "mutasi_debit_apr": row.get('mutasi_debit_apr', '').strip(),
                    "mutasi_debit_mei": row.get('mutasi_debit_mei', '').strip(),
                    "mutasi_debit_jun": row.get('mutasi_debit_jun', '').strip(),
                    "mutasi_kredit_apr": row.get('mutasi_kredit_apr', '').strip(),
                    "mutasi_kredit_mei": row.get('mutasi_kredit_mei', '').strip(),
                    "mutasi_kredit_jun": row.get('mutasi_kredit_jun', '').strip(),
                    "avg_mutasi_debit": row.get('avg_mutasi_debit', '').strip(),
                    "avg_mutasi_kredit": row.get('avg_mutasi_kredit', '').strip(),
                    "product_score": row.get('product_score', '').strip(),
                    "balance_score": row.get('balance_score', '').strip(),
                    "debit_score": row.get('debit_score', '').strip(),
                    "kredit_score": row.get('kredit_score', '').strip(),
                    "sme_opportunity_score": row.get('sme_opportunity_score', '').strip(),
                    "link_chat_1": row.get('link_chat_1', '').strip(),
                    "jawaban": row.get('jawaban', '').strip(),
                    "link_chat_2": row.get('link_chat_2', '').strip()
                })
                added += 1
        return jsonify({"status": "ok", "added": added})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@app.route('/api/recipients/replace', methods=['POST'])
def replace_recipients():
    global DATABASE_PENERIMA
    file = request.files.get('file')
    if file:
        try:
            import csv, io
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            reader = csv.DictReader(stream)
            new_data = []
            for row in reader:
                if row.get('nama') and row.get('kontak'):
                    new_data.append({
                        "id": str(uuid.uuid4()),
                        "nama": row.get('nama', '').strip(),
                        "kontak": row.get('kontak', '').strip(),
                        "kategori": row.get('kategori', 'Low Potential').strip(),
                        "end_balance": row.get('end_balance', '').strip(),
                        "giro": row.get('giro', '').strip(),
                        "deposito": row.get('deposito', '').strip(),
                        "dpk": row.get('dpk', '').strip(),
                        "mutasi_debit_apr": row.get('mutasi_debit_apr', '').strip(),
                        "mutasi_debit_mei": row.get('mutasi_debit_mei', '').strip(),
                        "mutasi_debit_jun": row.get('mutasi_debit_jun', '').strip(),
                        "mutasi_kredit_apr": row.get('mutasi_kredit_apr', '').strip(),
                        "mutasi_kredit_mei": row.get('mutasi_kredit_mei', '').strip(),
                        "mutasi_kredit_jun": row.get('mutasi_kredit_jun', '').strip(),
                        "avg_mutasi_debit": row.get('avg_mutasi_debit', '').strip(),
                        "avg_mutasi_kredit": row.get('avg_mutasi_kredit', '').strip(),
                        "product_score": row.get('product_score', '').strip(),
                        "balance_score": row.get('balance_score', '').strip(),
                        "debit_score": row.get('debit_score', '').strip(),
                        "kredit_score": row.get('kredit_score', '').strip(),
                        "sme_opportunity_score": row.get('sme_opportunity_score', '').strip(),
                        "link_chat_1": row.get('link_chat_1', '').strip(),
                        "jawaban": row.get('jawaban', '').strip(),
                        "link_chat_2": row.get('link_chat_2', '').strip()
                    })
            DATABASE_PENERIMA = new_data
            return jsonify({"status": "ok", "total": len(new_data)})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400
    data = request.json or {}
    recipients = data.get('recipients', [])
    if not isinstance(recipients, list):
        return jsonify({"status": "error", "error": "recipients harus berupa array"}), 400
    new_data = []
    for r in recipients:
        rid = r.get('id') or str(uuid.uuid4())
        new_data.append({
            "id": str(rid),
            "nama": r.get('nama', r.get('Nama', '')),
            "kontak": r.get('kontak', r.get('Kontak', r.get('No. WhatsApp', r.get('Nomor WhatsApp', '')))),
            "kategori": r.get('kategori', r.get('Kategori', 'Low Potential')),
            "end_balance": r.get('end_balance', r.get('End Balance Tabungan', '')),
            "giro": r.get('giro', r.get('Giro', '')),
            "deposito": r.get('deposito', r.get('Deposito', '')),
            "dpk": r.get('dpk', r.get('DPK', '')),
            "mutasi_debit_apr": r.get('mutasi_debit_apr', r.get('Mutasi Debit April', '')),
            "mutasi_debit_mei": r.get('mutasi_debit_mei', r.get('Mutasi Debit Mei', '')),
            "mutasi_debit_jun": r.get('mutasi_debit_jun', r.get('Mutasi Debit Juni', '')),
            "mutasi_kredit_apr": r.get('mutasi_kredit_apr', r.get('Mutasi Kredit April', '')),
            "mutasi_kredit_mei": r.get('mutasi_kredit_mei', r.get('Mutasi Kredit Mei', '')),
            "mutasi_kredit_jun": r.get('mutasi_kredit_jun', r.get('Mutasi Kredit Juni', '')),
            "avg_mutasi_debit": r.get('avg_mutasi_debit', r.get('Avg Mutasi Debit', '')),
            "avg_mutasi_kredit": r.get('avg_mutasi_kredit', r.get('Avg Mutasi Kredit', '')),
            "product_score": r.get('product_score', r.get('Product Score', '')),
            "balance_score": r.get('balance_score', r.get('Balance Score', '')),
            "debit_score": r.get('debit_score', r.get('Debit Score', '')),
            "kredit_score": r.get('kredit_score', r.get('Kredit Score', '')),
            "sme_opportunity_score": r.get('sme_opportunity_score', r.get('SME Opportunity Score', '')),
            "link_chat_1": r.get('link_chat_1', r.get('Link Chat 1', '')),
            "jawaban": r.get('jawaban', r.get('Jawaban', '')),
            "link_chat_2": r.get('link_chat_2', r.get('Link Chat 2', ''))
        })
    DATABASE_PENERIMA = new_data
    return jsonify({"status": "ok", "total": len(new_data)})


GOOGLE_SHEET_CSV_URL = os.environ.get('GOOGLE_SHEET_CSV_URL', '')


@app.route('/api/recipients/sync-sheets', methods=['POST'])
def sync_google_sheets():
    global DATABASE_PENERIMA
    csv_url = request.json.get('csv_url') if request.json else None
    if not csv_url:
        csv_url = GOOGLE_SHEET_CSV_URL
    if not csv_url:
        return jsonify({"status": "error", "error": "CSV URL tidak dikonfigurasi. Set variabel GOOGLE_SHEET_CSV_URL atau kirim csv_url di body."}), 400
    try:
        resp = req_lib.get(csv_url, timeout=30)
        resp.raise_for_status()
        stream = io.StringIO(resp.text)
        reader = csv.DictReader(stream)
        new_data = []
        for row in reader:
            row_stripped = {k.strip(): v.strip() for k, v in row.items()}
            nama = row_stripped.get('Nama Nasabah', '')
            kontak = row_stripped.get('No. WhatsApp ', row_stripped.get('No. WhatsApp', '')).strip()
            kategori_raw = row_stripped.get('Kategori', 'Low Potential')
            kategori = kategori_raw.replace('🔥 High Potential', 'High Potential').replace('🟡 Medium Potential', 'Medium Potential').replace('⚪ Low Potential', 'Low Potential').strip()
            if nama and kontak:
                new_data.append({
                    "id": str(uuid.uuid4()),
                    "nama": nama,
                    "kontak": kontak,
                    "kategori": kategori,
                    "end_balance": row_stripped.get('End Balance Tabungan', '').strip(),
                    "giro": row_stripped.get('Giro', '').strip(),
                    "deposito": row_stripped.get('Deposito', '').strip(),
                    "dpk": row_stripped.get('DPK', '').strip(),
                    "mutasi_debit_apr": row_stripped.get('Mutasi Debit April', '').strip(),
                    "mutasi_debit_mei": row_stripped.get('Mutasi Debit Mei', '').strip(),
                    "mutasi_debit_jun": row_stripped.get('Mutasi Debit Juni', '').strip(),
                    "mutasi_kredit_apr": row_stripped.get('Mutasi Kredit April', '').strip(),
                    "mutasi_kredit_mei": row_stripped.get('Mutasi Kredit Mei', '').strip(),
                    "mutasi_kredit_jun": row_stripped.get('Mutasi Kredit Juni', '').strip(),
                    "avg_mutasi_debit": row_stripped.get('Avg Mutasi Debit ', row_stripped.get('Avg Mutasi Debit', '')).strip(),
                    "avg_mutasi_kredit": row_stripped.get('Avg Mutasi Kredit ', row_stripped.get('Avg Mutasi Kredit', '')).strip(),
                    "product_score": row_stripped.get('Product Score ', row_stripped.get('Product Score', '')).strip(),
                    "balance_score": row_stripped.get('Balance Score ', row_stripped.get('Balance Score', '')).strip(),
                    "debit_score": row_stripped.get('Debit Score ', row_stripped.get('Debit Score', '')).strip(),
                    "kredit_score": row_stripped.get('Kredit Score ', row_stripped.get('Kredit Score', '')).strip(),
                    "sme_opportunity_score": row_stripped.get('SME Opportunity Score ', row_stripped.get('SME Opportunity Score', '')).strip(),
                    "link_chat_1": row_stripped.get('Link Chat 1 ', row_stripped.get('Link Chat 1', '')).strip(),
                    "jawaban": row_stripped.get('Jawaban ', row_stripped.get('Jawaban', '')).strip(),
                    "link_chat_2": row_stripped.get('Link Chat 2 ', row_stripped.get('Link Chat 2', '')).strip()
                })
        DATABASE_PENERIMA = new_data
        return jsonify({"status": "ok", "total": len(new_data)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@app.route('/api/history')
def get_history():
    return jsonify({"history": CAMPAIGN_HISTORY})


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify({"settings": get_settings()})
    data = request.json or {}
    save_settings_file(data.get('settings', {}))
    return jsonify({"status": "ok"})


@app.route('/api/blast', methods=['POST'])
def send_blast():
    data = request.json or {}
    recipient_ids = data.get('recipient_ids', [])
    pesan_template = data.get('pesan', '')

    settings = get_settings()
    provider = settings.get('provider', 'mock')
    api_key = settings.get('apiKey', '')
    sender_number = settings.get('senderNumber', '')

    target_penerima = []
    for p in DATABASE_PENERIMA:
        if recipient_ids and p['id'] not in recipient_ids:
            continue
        pesan_personal = pesan_template
        for key in ['nama', 'region', 'kategori', 'kontak', 'id', 'sme_opportunity_score']:
            pesan_personal = pesan_personal.replace("{" + key + "}", p.get(key, ''))
        result = send_message_via_provider(provider, pesan_personal, p['kontak'], api_key, sender_number)
        status = result.get('status', 'failed').capitalize()
        if status == 'Sent' and provider == 'mock':
            status = 'Mock'
        target_penerima.append({
            "id": p['id'],
            "nama": p['nama'],
            "kontak": p['kontak'],
            "region": p.get('region', ''),
            "kategori": p.get('kategori', ''),
            "sme_opportunity_score": p.get('sme_opportunity_score', ''),
            "pesan_terkirim": pesan_personal,
            "status": status,
            "error": result.get('error', ''),
            "provider": result.get('provider', provider)
        })

    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total": len(target_penerima),
        "provider": provider,
        "details": target_penerima
    }
    CAMPAIGN_HISTORY.append(record)
    return jsonify({"status": "ok", "total_sent": len(target_penerima), "provider": provider, "details": target_penerima})


# PENTING: Ekspor variabel app secara eksplisit untuk Vercel Serverless
app = app

if __name__ == '__main__':
    app.run(debug=True)
