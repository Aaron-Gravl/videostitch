document.getElementById("processBtn").addEventListener("click", async () => {
    const hooks = document.getElementById("hooks").files;
    const bodies = document.getElementById("bodies").files;
    const ctas = document.getElementById("ctas").files;

    if (hooks.length === 0 || bodies.length === 0 || ctas.length === 0) {
        document.getElementById("status").innerText = "Please upload all required videos.";
        return;
    }

    // Prepare file data
    const formData = new FormData();
    for (const file of hooks) formData.append("hooks", file.name);
    for (const file of bodies) formData.append("bodies", file.name);
    for (const file of ctas) formData.append("ctas", file.name);

    document.getElementById("status").innerText = "Processing videos...";
    
    // Send process request
    const response = await fetch("/process", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            hooks: Array.from(hooks).map(file => file.name),
            bodies: Array.from(bodies).map(file => file.name),
            ctas: Array.from(ctas).map(file => file.name),
        }),
    });

    const result = await response.json();

    if (result.zip_path) {
        document.getElementById("status").innerHTML = `
            <a href="/download/${result.zip_path}" download>Download Processed Videos</a>
        `;
    } else {
        document.getElementById("status").innerText = "Error processing videos. Please try again.";
    }
});
