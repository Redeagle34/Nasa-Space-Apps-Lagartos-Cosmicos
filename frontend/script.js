// Frontend JavaScript for NASA Space Apps Project
const API_BASE_URL = 'http://localhost:5000/api';


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