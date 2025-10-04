// Frontend JavaScript for NASA Space Apps Project
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const dataForm = document.getElementById('dataForm');
const nameInput = document.getElementById('nameInput');
const messageInput = document.getElementById('messageInput');
const loadDataBtn = document.getElementById('loadDataBtn');
const dataContainer = document.getElementById('dataContainer');

// Add data to database
dataForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = nameInput.value.trim();
    const message = messageInput.value.trim();
    
    if (!name || !message) {
        showMessage('Please fill in both fields', 'error');
        return;
    }
    
    try {
        showMessage('Adding data...', 'loading');
        
        const response = await fetch(`${API_BASE_URL}/data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showMessage('Data added successfully!', 'success');
        nameInput.value = '';
        messageInput.value = '';
        
        // Auto-refresh the data display
        setTimeout(loadData, 1000);
        
    } catch (error) {
        console.error('Error adding data:', error);
        showMessage('Error adding data. Please check if backend is running.', 'error');
    }
});

// Load data from database
loadDataBtn.addEventListener('click', loadData);

async function loadData() {
    try {
        showMessage('Loading data...', 'loading');
        
        const response = await fetch(`${API_BASE_URL}/data`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayData(data);
        
    } catch (error) {
        console.error('Error loading data:', error);
        showMessage('Error loading data. Please check if backend is running.', 'error');
    }
}

function displayData(data) {
    if (!Array.isArray(data) || data.length === 0) {
        dataContainer.innerHTML = '<p class="loading">No data found in database</p>';
        return;
    }
    
    const dataHTML = data.map(item => `
        <div class="data-item">
            <strong>Name:</strong> ${escapeHtml(item.name)}<br>
            <strong>Message:</strong> ${escapeHtml(item.message)}<br>
            <small><strong>Added:</strong> ${new Date(item.createdAt).toLocaleString()}</small>
        </div>
    `).join('');
    
    dataContainer.innerHTML = dataHTML;
}

function showMessage(message, type) {
    dataContainer.innerHTML = `<p class="${type}">${escapeHtml(message)}</p>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

const testApiBtn = document.getElementById('testApiBtn');
const testApiResult = document.getElementById('testApiResult');

testApiBtn.addEventListener('click', async () => {
    testApiResult.textContent = 'Testing...';
    try {
        const response = await fetch('http://localhost:5000/api/message');
        if (!response.ok) throw new Error('Backend not reachable');
        const data = await response.json();
        testApiResult.textContent = 'Success: ' + data.message;
        testApiResult.style.color = 'green';
    } catch (err) {
        testApiResult.textContent = 'Failed to connect to backend!';
        testApiResult.style.color = 'red';
    }
});

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadData();
});