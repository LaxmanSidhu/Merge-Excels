const form = document.getElementById("uploadForm");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const resultBox = document.getElementById("result");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const downloadType = e.submitter.value;
    formData.append("download_type", downloadType);

    progressContainer.style.display = "block";
    progressBar.style.width = "0%";
    progressText.textContent = "Starting...";

    // Fake progress animation
    let progress = 0;
    const fakeProgress = setInterval(() => {
        if (progress < 70) {
            progress += Math.random() * 10;
        } else if (progress < 90) {
            progress += Math.random() * 3;
        } else if (progress < 97) {
            progress += Math.random() * 1;
        }
        progressBar.style.width = `${Math.min(progress, 97)}%`;

        if (progress < 90) {
            progressText.textContent = "Processing files...";
        } else if (!progressText.querySelector(".dot-loader")) {
            progressText.innerHTML = `Finalizing merged file <span class="dot-loader"><span></span><span></span><span></span></span>`;
        }
    }, 300);

    try {
        const response = await fetch("/merge", { method: "POST", body: formData });
        clearInterval(fakeProgress);
        progressBar.style.width = "100%";
        progressText.textContent = "Download ready ✅";

        if (!response.ok) throw new Error(await response.text() || "Error merging files");

        // Read blob + metadata
        const blob = await response.blob();
        const metadata = response.headers.get("X-Metadata");
        const meta = metadata ? JSON.parse(metadata) : null;

        if (meta) {
            resultBox.style.display = "block";
            resultBox.innerHTML = `
            <strong>✅ Merged Successfully!</strong><br><br>
            <b>Files Processed:</b><br>${meta.files.join("<br>")}<br><br>
            <b>Rows per File:</b><br>${meta.rows.join("<br>")}<br><br>
            <b>Total Rows:</b> ${meta.total_rows}<br>
            <b>Total Columns:</b> ${meta.total_cols}
          `;
        }

        // Trigger download
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `merged_feedspot.${downloadType === "excel" ? "xlsx" : "csv"}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        clearInterval(fakeProgress);
        progressText.textContent = "❌ Error: " + err.message;
    }
});