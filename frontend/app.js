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

const fileInput = document.getElementById("fileInput");

const uploadArea = document.getElementById("uploadArea");

const browseButton = document.getElementById("browseButton");

const fileNameElement = document.getElementById("fileName");

const analyzeButton = document.getElementById("analyzeButton");

const analysisScreen = document.getElementById("analysisScreen");

const statusElement = document.getElementById("status");

const themeToggle = document.getElementById("themeToggle");

// ---------------------------------------------------------
// STATE
// ---------------------------------------------------------

let selectedFile = null;

// =========================================================
// THEME
// =========================================================

function initializeTheme() {
  const savedTheme = localStorage.getItem("medify-theme");

  if (savedTheme === "dark") {
    document.body.classList.add("dark");
  }
}

if (themeToggle) {
  themeToggle.addEventListener("click", function () {
    document.body.classList.toggle("dark");

    const isDark = document.body.classList.contains("dark");

    localStorage.setItem("medify-theme", isDark ? "dark" : "light");
  });
}

initializeTheme();

// =========================================================
// FILE SELECTION
// =========================================================

if (browseButton && fileInput) {
  browseButton.addEventListener("click", function (event) {
    event.preventDefault();

    fileInput.click();
  });
}

if (fileInput) {
  fileInput.addEventListener("change", function () {
    if (!fileInput.files || fileInput.files.length === 0) {
      return;
    }

    handleFile(fileInput.files[0]);
  });
}

// =========================================================
// DRAG & DROP
// =========================================================

if (uploadArea) {
  uploadArea.addEventListener("dragover", function (event) {
    event.preventDefault();

    uploadArea.classList.add("dragging");
  });

  uploadArea.addEventListener("dragleave", function () {
    uploadArea.classList.remove("dragging");
  });

  uploadArea.addEventListener("drop", function (event) {
    event.preventDefault();

    uploadArea.classList.remove("dragging");

    const files = event.dataTransfer.files;

    if (!files || files.length === 0) {
      return;
    }

    handleFile(files[0]);
  });
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

  const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];

  if (!allowedTypes.includes(file.type)) {
    showStatus("Please upload a JPG, PNG, WEBP image.", "error");

    return;
  }

  // -----------------------------------------------------
  // FILE SIZE CHECK
  // -----------------------------------------------------
  //
  // Backend limit is 10 MB.
  // Keep frontend validation consistent.
  //

  const maxSize = 10 * 1024 * 1024;

  if (file.size > maxSize) {
    showStatus("The file must be smaller than 10 MB.", "error");

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
    fileNameElement.textContent = `Selected: ${file.name}`;
  }

  if (uploadArea) {
    uploadArea.classList.add("file-selected");
  }

  showStatus("Report selected successfully.", "success");
}

// =========================================================
// ANALYZE BUTTON
// =========================================================

if (analyzeButton) {
  analyzeButton.addEventListener("click", analyzeReport);
}

// =========================================================
// ANALYSIS STAGE CONTROLLER
// =========================================================
//
// Backend stage names:
//
// extract
// understand
// analyze
// prepare
//
// The backend sends:
//
// active
// complete
//
// This function converts those events into the visual
// four-card timeline.
//

function updateAnalysisStage(stages, stageName, status) {
  if (!stages || stages.length === 0) {
    return;
  }

  const stageOrder = ["extract", "understand", "analyze", "prepare"];

  const currentIndex = stageOrder.indexOf(stageName);

  if (currentIndex === -1) {
    console.warn("Unknown analysis stage:", stageName);

    return;
  }

  stages.forEach(function (stage, index) {
    stage.classList.remove("active", "done");

    // -------------------------------------------------
    // PREVIOUS STAGES
    // -------------------------------------------------

    if (index < currentIndex) {
      stage.classList.add("done");

      return;
    }

    // -------------------------------------------------
    // CURRENT ACTIVE STAGE
    // -------------------------------------------------

    if (index === currentIndex && status === "active") {
      stage.classList.add("active");

      return;
    }

    // -------------------------------------------------
    // CURRENT COMPLETED STAGE
    // -------------------------------------------------

    if (index === currentIndex && status === "complete") {
      stage.classList.add("done");
    }
  });
}

// =========================================================
// RESET ANALYSIS STAGES
// =========================================================

function resetAnalysisStages(stages) {
  if (!stages || stages.length === 0) {
    return;
  }

  stages.forEach(function (stage) {
    stage.classList.remove("active", "done");
  });

  // First stage starts immediately.
  stages[0]?.classList.add("active");
}

// =========================================================
// PROCESS ONE STREAM EVENT
// =========================================================
//
// Every backend line is a JSON object.
//
// Example:
//
// {
//     "type": "stage",
//     "stage": "extract",
//     "status": "active"
// }
//
// or:
//
// {
//     "type": "complete",
//     "data": {...}
// }
//

function processAnalysisEvent(event, stages) {
  if (!event || typeof event !== "object") {
    return null;
  }

  // -----------------------------------------------------
  // ERROR EVENT
  // -----------------------------------------------------

  if (event.type === "error") {
    throw new Error(
      event.message || "The medical report could not be analyzed.",
    );
  }

  // -----------------------------------------------------
  // STAGE EVENT
  // -----------------------------------------------------

  if (event.type === "stage") {
    updateAnalysisStage(stages, event.stage, event.status);

    console.log("Analysis stage:", event.stage, event.status);

    return null;
  }

  // -----------------------------------------------------
  // FINAL EVENT
  // -----------------------------------------------------

  if (event.type === "complete") {
    updateAnalysisStage(stages, "prepare", "complete");

    return event.data || null;
  }

  return null;
}

// =========================================================
// ANALYZE REPORT
// =========================================================

async function analyzeReport() {
  // -----------------------------------------------------
  // CHECK FILE
  // -----------------------------------------------------

  if (!selectedFile) {
    showStatus("Please upload a medical report first.", "error");

    return;
  }

  // -----------------------------------------------------
  // ANALYSIS SCREEN
  // -----------------------------------------------------

  if (analysisScreen) {
    analysisScreen.classList.add("active");

    document.body.classList.add("analysis-active");

    analysisScreen.setAttribute("aria-busy", "true");
  }

  // -----------------------------------------------------
  // GET ANALYSIS STAGES
  // -----------------------------------------------------

  const stages = document.querySelectorAll("#analysisScreen .stage");

  // -----------------------------------------------------
  // RESET STAGES
  // -----------------------------------------------------

  resetAnalysisStages(stages);

  // -----------------------------------------------------
  // DISABLE BUTTON
  // -----------------------------------------------------

  analyzeButton.disabled = true;

  const originalButtonHTML = analyzeButton.innerHTML;

  analyzeButton.innerHTML = `
        <span class="loading-spinner"></span>
        Analyzing report...
    `;

  showStatus("Reading your medical report...", "loading");

  // -----------------------------------------------------
  // FORM DATA
  // -----------------------------------------------------

  const formData = new FormData();

  formData.append("file", selectedFile);

  try {
    // =================================================
    // SEND TO BACKEND
    // =================================================

    const response = await fetch(`${API_BASE_URL}/analyze-report`, {
      method: "POST",
      body: formData,
    });

    // =================================================
    // HTTP ERROR
    // =================================================

    if (!response.ok) {
      let errorMessage = "The report could not be analyzed.";

      try {
        const errorText = await response.text();

        if (errorText) {
          try {
            const errorJSON = JSON.parse(errorText);

            errorMessage =
              errorJSON?.detail || errorJSON?.message || errorMessage;
          } catch (_) {
            errorMessage = errorText;
          }
        }
      } catch (_) {
        // Keep default message.
      }

      throw new Error(errorMessage);
    }

    // =================================================
    // STREAM SUPPORT CHECK
    // =================================================

    if (!response.body) {
      throw new Error(
        "The browser could not read the streamed analysis response.",
      );
    }

    // =================================================
    // CREATE STREAM READER
    // =================================================

    const reader = response.body.getReader();

    const decoder = new TextDecoder("utf-8");

    let buffer = "";

    let finalResult = null;

    // =================================================
    // READ STREAM
    // =================================================

    while (true) {
      const { value, done } = await reader.read();

      // -------------------------------------------------
      // STREAM FINISHED
      // -------------------------------------------------

      if (done) {
        break;
      }

      // -------------------------------------------------
      // DECODE CHUNK
      // -------------------------------------------------

      buffer += decoder.decode(value, {
        stream: true,
      });

      // -------------------------------------------------
      // SPLIT INTO LINES
      // -------------------------------------------------
      //
      // Backend uses NDJSON:
      //
      // JSON\n
      // JSON\n
      // JSON\n
      //

      const lines = buffer.split("\n");

      // Last item may be incomplete.
      buffer = lines.pop() || "";

      // -------------------------------------------------
      // PROCESS COMPLETE LINES
      // -------------------------------------------------

      for (const line of lines) {
        const trimmed = line.trim();

        if (!trimmed) {
          continue;
        }

        let event;

        try {
          event = JSON.parse(trimmed);
        } catch (parseError) {
          console.warn("Could not parse analysis event:", trimmed);

          continue;
        }

        const eventResult = processAnalysisEvent(event, stages);

        if (eventResult) {
          finalResult = eventResult;
        }
      }
    }

    // =================================================
    // FLUSH TEXT DECODER
    // =================================================

    buffer += decoder.decode();

    // =================================================
    // PROCESS FINAL BUFFER
    // =================================================

    if (buffer.trim()) {
      const finalLines = buffer.split("\n");

      for (const line of finalLines) {
        const trimmed = line.trim();

        if (!trimmed) {
          continue;
        }

        let event;

        try {
          event = JSON.parse(trimmed);
        } catch (parseError) {
          console.warn("Could not parse final analysis event:", trimmed);

          continue;
        }

        const eventResult = processAnalysisEvent(event, stages);

        if (eventResult) {
          finalResult = eventResult;
        }
      }
    }

    // =================================================
    // VALIDATE FINAL RESULT
    // =================================================

    if (!finalResult) {
      throw new Error("The analysis finished without returning a result.");
    }

    if (typeof finalResult !== "object") {
      throw new Error("The backend returned an invalid analysis result.");
    }

    // =================================================
    // LOG RESULT
    // =================================================

    console.log("Medical report analysis:", finalResult);

    // =================================================
    // SAVE COMPLETE RESPONSE
    // =================================================

    sessionStorage.setItem("medifyReport", JSON.stringify(finalResult));

    // =================================================
    // SAVE ORIGINAL FILE NAME
    // =================================================

    sessionStorage.setItem(
      "medifyReportFilename",
      selectedFile?.name || finalResult.filename || "Medical Report",
    );

    // =================================================
    // MARK ANALYSIS SCREEN READY
    // =================================================

    if (analysisScreen) {
      analysisScreen.setAttribute("aria-busy", "false");
    }

    // =================================================
    // SUCCESS MESSAGE
    // =================================================

    showStatus("Report analyzed successfully. Opening results...", "success");

    /* =================================================
   ANALYSIS → RESULTS TRANSITION
================================================= */

    if (analysisScreen) {
      analysisScreen.classList.add("leaving");
    }

    /* Preserve the currently selected theme during navigation */
    const currentTheme = document.body.classList.contains("dark")
      ? "dark"
      : "light";

    localStorage.setItem("medify-theme", currentTheme);

    sessionStorage.setItem("medifyTheme", currentTheme);

    /*
     * Store a flag so results.html knows that it was
     * opened directly from the analysis experience.
     */

    sessionStorage.setItem("medifyAnalysisTransition", "true");

    /*
     * Give the exit animation enough time to finish
     * before navigating to the results page.
     */

    await new Promise(function (resolve) {
      setTimeout(resolve, 550);
    });

    /* =================================================
   GO TO RESULTS PAGE
================================================= */

    window.location.href = "results.html";
  } catch (error) {
    // =================================================
    // LOG ERROR
    // =================================================

    console.error("Report analysis error:", error);

    // =================================================
    // HIDE ANALYSIS SCREEN
    // =================================================

    if (analysisScreen) {
      analysisScreen.classList.remove("active");

      analysisScreen.setAttribute("aria-busy", "false");
    }

    document.body.classList.remove("analysis-active");

    // =================================================
    // RESTORE BUTTON
    // =================================================

    analyzeButton.innerHTML = originalButtonHTML;

    analyzeButton.disabled = false;

    // =================================================
    // SHOW ERROR
    // =================================================

    showStatus(
      error.message || "Something went wrong while analyzing the report.",
      "error",
    );
  }
}

// =========================================================
// STATUS MESSAGE
// =========================================================

function showStatus(message, type = "info") {
  if (!statusElement) {
    return;
  }

  statusElement.textContent = message;

  // -----------------------------------------------------
  // RESET CLASSES
  // -----------------------------------------------------

  statusElement.classList.remove("success", "error", "loading");

  // -----------------------------------------------------
  // APPLY TYPE
  // -----------------------------------------------------

  if (type) {
    statusElement.classList.add(type);
  }
}

// =========================================================
// OPTIONAL: CLICK UPLOAD AREA
// =========================================================

if (uploadArea && fileInput) {
  uploadArea.addEventListener("click", function (event) {
    // Don't trigger the file dialog when clicking
    // the Browse button itself.

    if (event.target === browseButton || browseButton?.contains(event.target)) {
      return;
    }

    fileInput.click();
  });
}

// =========================================================
// OPTIONAL: KEYBOARD ACCESSIBILITY
// =========================================================

if (uploadArea && fileInput) {
  uploadArea.setAttribute("tabindex", "0");

  uploadArea.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();

      fileInput.click();
    }
  });
}

// =========================================================
// PREVENT ACCIDENTAL FORM SUBMISSION
// =========================================================

const uploadForm = document.querySelector("form");

if (uploadForm) {
  uploadForm.addEventListener("submit", function (event) {
    event.preventDefault();

    analyzeReport();
  });
}

// =========================================================
// NAVBAR SCROLL EFFECT
// =========================================================

const navbar = document.querySelector(".navbar");

if (navbar) {
  function updateNavbar() {
    if (window.scrollY > 45) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  }

  window.addEventListener("scroll", updateNavbar, {
    passive: true,
  });

  updateNavbar();
}
