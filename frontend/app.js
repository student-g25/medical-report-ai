// =========================================================
// MEDIFY — FRONTEND APP
// =========================================================

// ---------------------------------------------------------
// API CONFIGURATION
// ---------------------------------------------------------

const API_BASE_URL = "https://medical-report-ai-a6s6.onrender.com";

// ---------------------------------------------------------
// DOM ELEMENTS
// ---------------------------------------------------------

const fileInput =
    document.getElementById("fileInput");

const uploadArea =
    document.getElementById("uploadArea");

const browseButton =
    document.getElementById("browseButton");

const fileNameElement =
    document.getElementById("fileName");

const analyzeButton =
    document.getElementById("analyzeButton");

const statusElement =
    document.getElementById("status");

const themeToggle =
    document.getElementById("themeToggle");


// ---------------------------------------------------------
// STATE
// ---------------------------------------------------------

let selectedFile = null;


// =========================================================
// THEME
// =========================================================

function initializeTheme() {

    const savedTheme =
        localStorage.getItem("medify-theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark");
    }
}


if (themeToggle) {

    themeToggle.addEventListener(
        "click",
        function () {

            document.body.classList.toggle("dark");

            const isDark =
                document.body.classList.contains("dark");

            localStorage.setItem(
                "medify-theme",
                isDark ? "dark" : "light"
            );
        }
    );
}


initializeTheme();


// =========================================================
// FILE SELECTION
// =========================================================

if (browseButton && fileInput) {

    browseButton.addEventListener(
        "click",
        function (event) {

            event.preventDefault();

            fileInput.click();
        }
    );
}


if (fileInput) {

    fileInput.addEventListener(
        "change",
        function () {

            if (!fileInput.files ||
                fileInput.files.length === 0) {

                return;
            }

            handleFile(
                fileInput.files[0]
            );
        }
    );
}


// =========================================================
// DRAG & DROP
// =========================================================

if (uploadArea) {

    uploadArea.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadArea.classList.add(
                "dragging"
            );
        }
    );


    uploadArea.addEventListener(
        "dragleave",
        function () {

            uploadArea.classList.remove(
                "dragging"
            );
        }
    );


    uploadArea.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            uploadArea.classList.remove(
                "dragging"
            );

            const files =
                event.dataTransfer.files;

            if (!files ||
                files.length === 0) {

                return;
            }

            handleFile(files[0]);
        }
    );
}


// =========================================================
// HANDLE FILE
// =========================================================

function handleFile(file) {

    if (!file) {
        return;
    }


    // -----------------------------------------------------
    // FILE TYPE CHECK
    // -----------------------------------------------------

    const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    ];


    if (!allowedTypes.includes(file.type)) {

        showStatus(
            "Please upload a JPG, PNG, WEBP image.",
            "error"
        );

        return;
    }


    // -----------------------------------------------------
    // FILE SIZE CHECK
    // -----------------------------------------------------

    const maxSize =
        20 * 1024 * 1024;


    if (file.size > maxSize) {

        showStatus(
            "The file must be smaller than 20 MB.",
            "error"
        );

        return;
    }


    // -----------------------------------------------------
    // SAVE FILE
    // -----------------------------------------------------

    selectedFile = file;


    // -----------------------------------------------------
    // UPDATE UI
    // -----------------------------------------------------

    if (fileNameElement) {

        fileNameElement.textContent =
            `Selected: ${file.name}`;
    }


    if (uploadArea) {

        uploadArea.classList.add(
            "file-selected"
        );
    }


    showStatus(
        "Report selected successfully.",
        "success"
    );
}


// =========================================================
// ANALYZE BUTTON
// =========================================================

if (analyzeButton) {

    analyzeButton.addEventListener(
        "click",
        analyzeReport
    );
}


// =========================================================
// ANALYZE REPORT
// =========================================================

async function analyzeReport() {

    // -----------------------------------------------------
    // CHECK FILE
    // -----------------------------------------------------

    if (!selectedFile) {

        showStatus(
            "Please upload a medical report first.",
            "error"
        );

        return;
    }


    // -----------------------------------------------------
    // DISABLE BUTTON
    // -----------------------------------------------------

    analyzeButton.disabled = true;

    const originalButtonHTML =
        analyzeButton.innerHTML;


    analyzeButton.innerHTML = `
        <span class="loading-spinner"></span>
        Analyzing report...
    `;


    showStatus(
        "Uploading and analyzing your report...",
        "loading"
    );


    // -----------------------------------------------------
    // FORM DATA
    // -----------------------------------------------------

    const formData =
        new FormData();

    formData.append(
        "file",
        selectedFile
    );


    try {

        // -------------------------------------------------
        // SEND TO BACKEND
        // -------------------------------------------------

        const response =
            await fetch(
                `${API_BASE_URL}/analyze-report`,
                {
                    method: "POST",
                    body: formData
                }
            );


        // -------------------------------------------------
        // READ RESPONSE
        // -------------------------------------------------

        let result;

        try {

            result =
                await response.json();

        } catch (jsonError) {

            throw new Error(
                "The server returned an invalid response."
            );
        }


        // -------------------------------------------------
        // BACKEND ERROR
        // -------------------------------------------------

        if (!response.ok) {

            const backendMessage =
                result?.detail ||
                result?.message ||
                "The report could not be analyzed.";

            throw new Error(
                backendMessage
            );
        }


        // -------------------------------------------------
        // BASIC RESPONSE VALIDATION
        // -------------------------------------------------

        if (!result ||
            typeof result !== "object") {

            throw new Error(
                "The backend returned an empty result."
            );
        }


        // -------------------------------------------------
        // SAVE COMPLETE BACKEND RESPONSE
        // -------------------------------------------------
        //
        // IMPORTANT:
        //
        // We do NOT modify the backend response.
        //
        // The complete JSON returned by FastAPI is stored
        // temporarily in sessionStorage.
        //
        // results.html will read this data and dynamically
        // create the explanatory report.
        // -------------------------------------------------

        sessionStorage.setItem(
            "medifyReport",
            JSON.stringify(result)
        );


        // -------------------------------------------------
        // SAVE ORIGINAL FILE NAME
        // -------------------------------------------------

        sessionStorage.setItem(
            "medifyReportFilename",
            selectedFile?.name ||
            result.filename ||
            "Medical Report"
        );


        // -------------------------------------------------
        // SUCCESS
        // -------------------------------------------------

        showStatus(
            "Report analyzed successfully. Opening results...",
            "success"
        );


        // -------------------------------------------------
        // GO TO RESULTS PAGE
        // -------------------------------------------------

        setTimeout(
            function () {

                window.location.href =
                    "results.html";

            },
            300
        );


    } catch (error) {

        console.error(
            "Report analysis error:",
            error
        );


        showStatus(
            error.message ||
            "Something went wrong while analyzing the report.",
            "error"
        );


        // -------------------------------------------------
        // RESTORE BUTTON
        // -------------------------------------------------

        analyzeButton.innerHTML =
            originalButtonHTML;

        analyzeButton.disabled =
            false;
    }
}


// =========================================================
// STATUS MESSAGE
// =========================================================

function showStatus(
    message,
    type = "info"
) {

    if (!statusElement) {
        return;
    }


    statusElement.textContent =
        message;


    // -----------------------------------------------------
    // RESET CLASSES
    // -----------------------------------------------------

    statusElement.classList.remove(
        "success",
        "error",
        "loading"
    );


    if (type) {

        statusElement.classList.add(
            type
        );
    }
}


// =========================================================
// OPTIONAL: CLICK UPLOAD AREA
// =========================================================

if (uploadArea && fileInput) {

    uploadArea.addEventListener(
        "click",
        function (event) {

            // Don't trigger the file dialog when clicking
            // the Browse button itself.

            if (
                event.target === browseButton ||
                browseButton?.contains(event.target)
            ) {
                return;
            }


            fileInput.click();
        }
    );
}


// =========================================================
// OPTIONAL: KEYBOARD ACCESSIBILITY
// =========================================================

if (uploadArea && fileInput) {

    uploadArea.setAttribute(
        "tabindex",
        "0"
    );


    uploadArea.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" ||
                event.key === " "
            ) {

                event.preventDefault();

                fileInput.click();
            }
        }
    );
}


// =========================================================
// PREVENT ACCIDENTAL FORM SUBMISSION
// =========================================================

const uploadForm =
    document.querySelector("form");

if (uploadForm) {

    uploadForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();

            analyzeReport();
        }
    );
}


// =========================================================
// NAVBAR SCROLL EFFECT
// =========================================================

const navbar =
    document.querySelector(".navbar");


if (navbar) {

    function updateNavbar() {

        if (window.scrollY > 45) {

            navbar.classList.add(
                "scrolled"
            );

        } else {

            navbar.classList.remove(
                "scrolled"
            );
        }
    }


    window.addEventListener(
        "scroll",
        updateNavbar,
        {
            passive: true
        }
    );


    updateNavbar();
}