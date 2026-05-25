// DOM Elements
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('cv-upload');
const fileNameDisplay = document.getElementById('file-name');
const jdInput = document.getElementById('jd-input');
const cvTextInput = document.getElementById('cv-text-input');
const analyzeBtn = document.getElementById('analyze-btn');

const emptyState = document.getElementById('empty-state');
const loadingState = document.getElementById('loading-state');
const resultsDisplay = document.getElementById('results-display');

const scoreText = document.getElementById('score-text');
const scoreCircle = document.getElementById('score-circle');
const scoreTitle = document.getElementById('score-title');
const scoreDesc = document.getElementById('score-description');
const resultJobTitle = document.getElementById('result-job-title');
const resetBtn = document.getElementById('reset-btn');

let selectedFile = null;

// File Upload Handlers
uploadZone.addEventListener('click', () => fileInput.click());

// Drag and Drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadZone.addEventListener(eventName, preventDefaults, false);
});
function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

['dragenter', 'dragover'].forEach(eventName => {
    uploadZone.addEventListener(eventName, () => uploadZone.classList.add('border-primary', 'bg-muted/50'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('border-primary', 'bg-muted/50'), false);
});

uploadZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt.files && dt.files[0]) handleFile(dt.files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
});

function handleFile(file) {
    const validTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
    const validExtensions = [".pdf", ".docx", ".txt"];
    const isValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!validTypes.includes(file.type) && !isValidExt) {
        alert("Please upload a PDF, DOCX, or TXT file.");
        return;
    }
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileNameDisplay.classList.add('text-primary');
    uploadZone.classList.add('border-primary');
    if (cvTextInput) cvTextInput.value = ''; // clear text if file uploaded
}

if (cvTextInput) {
    cvTextInput.addEventListener('input', () => {
        if (cvTextInput.value.trim() !== '') {
            selectedFile = null;
            fileNameDisplay.textContent = 'Click or drag file here';
            fileNameDisplay.classList.remove('text-primary');
            uploadZone.classList.remove('border-primary');
            fileInput.value = '';
        }
    });
}

// Generate List Items HTML
function generateListHTML(items, iconColorClass) {
    if (!items || items.length === 0) return `<li class="text-sm text-muted-foreground italic">None identified.</li>`;
    return items.map(item => `
        <li class="flex items-start gap-3">
            <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-${iconColorClass} shrink-0"></span>
            <span class="text-sm text-muted-foreground leading-relaxed">${item}</span>
        </li>
    `).join('');
}

function generateSuggestionCards(items) {
    if (!items || items.length === 0) return `<div class="text-sm text-muted-foreground italic col-span-2">No recommendations.</div>`;
    return items.map(item => `
        <li class="bg-muted/10 border border-border rounded-lg p-4 flex gap-3">
            <span class="material-symbols-outlined text-blue-400 text-lg shrink-0 mt-0.5">info</span>
            <span class="text-sm text-muted-foreground">${item}</span>
        </li>
    `).join('');
}

function generateRedFlagCards(items) {
    if (!items || items.length === 0) return `<div class="text-sm text-muted-foreground italic col-span-2">No red flags detected. Great job!</div>`;
    return items.map(item => `
        <li class="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex gap-3">
            <span class="material-symbols-outlined text-red-500 text-lg shrink-0 mt-0.5">error</span>
            <span class="text-sm text-foreground">${item}</span>
        </li>
    `).join('');
}

// Analysis Execution
analyzeBtn.addEventListener('click', async () => {
    const cvTextValue = cvTextInput ? cvTextInput.value.trim() : '';
    
    if (!selectedFile && !cvTextValue) {
        alert("Please upload a Resume or paste your CV text.");
        return;
    }
    if (!jdInput.value.trim()) {
        alert("Please paste the Job Description.");
        return;
    }

    // UI State to Loading
    emptyState.classList.add('hidden');
    resultsDisplay.classList.add('hidden');
    loadingState.classList.remove('hidden');
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = `Analyzing <span class="material-symbols-outlined ml-2 text-[18px] animate-spin">refresh</span>`;

    const formData = new FormData();
    if (selectedFile) formData.append("cv", selectedFile);
    if (cvTextValue) formData.append("cv_text", cvTextValue);
    formData.append("jd", jdInput.value);

    try {
        const response = await fetch('/api/analyze', { method: 'POST', body: formData });
        const data = await response.json();
        
        if(data.error) throw new Error(data.error);

        // Populate Data
        const score = data.match_percentage || 0;
        scoreText.textContent = `${score}%`;
        
        // SVG Circle Math (Radius 54 = Circumference ~339.292)
        const circumference = 54 * 2 * Math.PI;
        const offset = circumference - (score / 100) * circumference;
        
        if (data.job_title) {
            resultJobTitle.textContent = data.job_title;
        } else {
            resultJobTitle.textContent = '';
        }

        // Color Logic
        scoreCircle.classList.remove('text-chart-1', 'text-chart-2', 'text-chart-3');
        if (score >= 75) {
            scoreCircle.classList.add('text-chart-1'); // Green
            scoreTitle.textContent = "Strong Match";
            scoreDesc.textContent = "This candidate has excellent alignment with the core requirements.";
        } else if (score >= 50) {
            scoreCircle.classList.add('text-chart-2'); // Yellow
            scoreTitle.textContent = "Moderate Match";
            scoreDesc.textContent = "This candidate has some overlapping skills, but notable gaps exist.";
        } else {
            scoreCircle.classList.add('text-chart-3'); // Red
            scoreTitle.textContent = "Weak Match";
            scoreDesc.textContent = "This candidate does not align well with the primary requirements.";
        }

        document.getElementById('list-strengths').innerHTML = generateListHTML(data.key_strengths, 'emerald-500');
        document.getElementById('list-gaps').innerHTML = generateListHTML(data.skill_gaps, 'amber-500');
        document.getElementById('list-red-flags').innerHTML = generateRedFlagCards(data.red_flags);
        document.getElementById('list-suggestions').innerHTML = generateSuggestionCards(data.suggestions);

        // UI State to Results
        loadingState.classList.add('hidden');
        resultsDisplay.classList.remove('hidden');
        
        // Scroll to results on mobile
        if (window.innerWidth < 768) {
            resultsDisplay.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Animate Circle after a tiny delay to ensure DOM is ready
        setTimeout(() => {
            scoreCircle.style.strokeDashoffset = offset;
        }, 50);

    } catch (e) {
        alert("Error during analysis: " + e.message);
        loadingState.classList.add('hidden');
        emptyState.classList.remove('hidden');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = `Analyze Resume <span class="material-symbols-outlined ml-2 text-[18px]">arrow_forward</span>`;
    }
});

// Reset Functionality
if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        selectedFile = null;
        if (fileInput) fileInput.value = '';
        if (cvTextInput) cvTextInput.value = '';
        if (jdInput) jdInput.value = '';
        if (fileNameDisplay) {
            fileNameDisplay.textContent = 'Click or drag file here';
            fileNameDisplay.classList.remove('text-primary');
        }
        if (uploadZone) uploadZone.classList.remove('border-primary');
        
        if (resultsDisplay) resultsDisplay.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}
