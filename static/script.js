document.getElementById("processBtn").addEventListener("click", async () => {
    const hooks = document.getElementById("hooks").files;
    const bodies = document.getElementById("bodies").files;
    const ctas = document.getElementById("ctas").files;

    const uploadFiles = async (files) => {
        const formData = new FormData();
        for (const file of files) {
            formData.append("file", file);
        }

        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Error uploading files");
        }

        return response.json();
    };

    try {
        // Step 1: Upload Hooks, Bodies, and CTAs
        document.getElementById("status").innerText = "Uploading files...";
        if (hooks.length > 0) await uploadFiles(hooks);
        if (bodies.length > 0) await uploadFiles(bodies);
        if (ctas.length > 0) await uploadFiles(ctas);

        // Step 2: Process Videos
        document.getElementById("status").innerText = "Processing videos...";
        const response = await fetch("/process", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                hooks: Array.from(hooks).map((file) => file.name),
                bodies: Array.from(bodies).map((file) => file.name),
                ctas: Array.from(ctas).map((file) => file.name),
            }),
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Error processing videos");
        }

        // Step 3: Provide Download Link
        document.getElementById("status").innerHTML = `
            <a href="/download/${result.zip_path}" download>Download Processed Videos</a>
        `;
    } catch (error) {
        document.getElementById("status").innerText = error.message;
    }
});
