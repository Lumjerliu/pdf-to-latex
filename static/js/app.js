/**
 * PDF to LaTeX Converter - Frontend JavaScript
 */

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const clearBtn = document.getElementById('clearBtn');
const selectedFile = document.getElementById('selectedFile');
const fileName = document.getElementById('fileName');
const backendSelect = document.getElementById('backend');
const backendHelp = document.getElementById('backendHelp');
const formatSelect = document.getElementById('format');
const convertBtn = document.getElementById('convertBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultSection = document.getElementById('resultSection');
const pagesProcessed = document.getElementById('pagesProcessed');
const outputFormat = document.getElementById('outputFormat');
const outputCode = document.getElementById('outputCode');
const codeLanguage = document.getElementById('codeLanguage');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const toggleWrapBtn = document.getElementById('toggleWrap');
const errorSection = document.getElementById('errorSection');
const errorText = document.getElementById('errorText');

// State
let currentFile = null;
let currentJobId = null;

// Backend descriptions
const backendDescriptions = {
    nougat: "Meta's model for scientific papers with math and tables",
    texify: "Excellent for math-heavy documents",
    pix2tex: "Specialized for math equations and single formulas"
};

// Event Listeners
selectBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
clearBtn.addEventListener('click', clearFile);
convertBtn.addEventListener('click', startConversion);
copyBtn.addEventListener('click', copyToClipboard);
downloadBtn.addEventListener('click', downloadResult);
toggleWrapBtn.addEventListener('click', toggleWrap);
backendSelect.addEventListener('change', updateBackendHelp);

// Drag and drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

dropZone.addEventListener('click', (e) => {
    if (e.target === dropZone || e.target.classList.contains('upload-icon')) {
        fileInput.click();
    }
});

// Functions
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError('Please select a PDF file');
        return;
    }
    
    currentFile = file;
    fileName.textContent = file.name;
    selectedFile.style.display = 'flex';
    convertBtn.disabled = false;
    hideError();
    hideResult();
}

function clearFile() {
    currentFile = null;
    fileInput.value = '';
    selectedFile.style.display = 'none';
    convertBtn.disabled = true;
    hideResult();
    hideError();
}

function updateBackendHelp() {
    const backend = backendSelect.value;
    backendHelp.textContent = backendDescriptions[backend] || '';
}

async function startConversion() {
    if (!currentFile) return;
    
    // Show loading state
    convertBtn.querySelector('.btn-text').style.display = 'none';
    convertBtn.querySelector('.btn-loading').style.display = 'inline-flex';
    convertBtn.disabled = true;
    
    showProgress();
    hideResult();
    hideError();
    
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('backend', backendSelect.value);
    formData.append('format', formatSelect.value);
    
    try {
        // Start conversion
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Conversion failed');
        }
        
        currentJobId = data.job_id;
        
        // Poll for status
        await pollStatus();
        
    } catch (error) {
        showError(error.message);
        resetConvertButton();
        hideProgress();
    }
}

async function pollStatus() {
    const maxAttempts = 120; // 2 minutes max
    let attempts = 0;
    
    const poll = async () => {
        attempts++;
        
        // Update progress animation
        const progress = Math.min((attempts / maxAttempts) * 100, 95);
        progressFill.style.width = `${progress}%`;
        
        try {
            const response = await fetch(`/api/status/${currentJobId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                if (data.success) {
                    showResult(data);
                } else {
                    showError(data.error || 'Conversion failed');
                }
                resetConvertButton();
                hideProgress();
                return;
            }
            
            if (data.status === 'failed') {
                showError(data.error || 'Conversion failed');
                resetConvertButton();
                hideProgress();
                return;
            }
            
            // Still processing
            progressText.textContent = `Processing... (${attempts}s)`;
            
            if (attempts < maxAttempts) {
                setTimeout(poll, 1000);
            } else {
                showError('Conversion timed out');
                resetConvertButton();
                hideProgress();
            }
            
        } catch (error) {
            showError('Failed to check conversion status');
            resetConvertButton();
            hideProgress();
        }
    };
    
    await poll();
}

function showResult(data) {
    resultSection.style.display = 'block';
    pagesProcessed.textContent = `${data.pages_processed} page(s)`;
    outputFormat.textContent = data.output_format;
    
    // Set code content
    outputCode.textContent = data.content;
    
    // Set language for highlighting
    const lang = data.output_format === 'latex' ? 'latex' : 'markdown';
    outputCode.className = `language-${lang}`;
    codeLanguage.textContent = lang;
    
    // Apply syntax highlighting
    hljs.highlightElement(outputCode);
    
    // Re-render MathJax if markdown
    if (data.output_format === 'markdown' && window.MathJax) {
        MathJax.typesetPromise([outputCode]).catch(err => console.log('MathJax error:', err));
    }
}

function hideResult() {
    resultSection.style.display = 'none';
}

function showProgress() {
    progressSection.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting conversion...';
}

function hideProgress() {
    progressSection.style.display = 'none';
}

function showError(message) {
    errorSection.style.display = 'block';
    errorText.textContent = message;
}

function hideError() {
    errorSection.style.display = 'none';
}

function resetConvertButton() {
    convertBtn.querySelector('.btn-text').style.display = 'inline';
    convertBtn.querySelector('.btn-loading').style.display = 'none';
    convertBtn.disabled = !currentFile;
}

async function copyToClipboard() {
    try {
        await navigator.clipboard.writeText(outputCode.textContent);
        
        const originalText = copyBtn.textContent;
        copyBtn.textContent = '✓ Copied!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
    }
}

function downloadResult() {
    if (!currentJobId) return;
    
    window.location.href = `/api/download/${currentJobId}`;
}

function toggleWrap() {
    outputCode.classList.toggle('wrap');
    const isWrapped = outputCode.classList.contains('wrap');
    toggleWrapBtn.textContent = isWrapped ? 'No Wrap' : 'Toggle Wrap';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check backend status
    fetch('/api/backends')
        .then(res => res.json())
        .then(backends => {
            Object.entries(backends).forEach(([key, info]) => {
                const option = backendSelect.querySelector(`option[value="${key}"]`);
                if (option && !info.installed) {
                    option.textContent += ' (not installed)';
                }
            });
        })
        .catch(err => console.log('Could not check backend status'));
});
