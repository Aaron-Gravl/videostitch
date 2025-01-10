document.getElementById('processBtn').addEventListener('click', async () => {
    const hooks = document.getElementById('hooks').files;
    const bodies = document.getElementById('bodies').files;
    const ctas = document.getElementById('ctas').files;

    const uploadFile = async (file, type) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`/upload?user_id=default_user&type=${type}`, {
            method: 'POST',
            body: formData,
        });
        return response.json();
    };

    for (const file of hooks) await uploadFile(file, 'hooks');
    for (const file of bodies) await uploadFile(file, 'bodies');
    for (const file of ctas) await uploadFile(file, 'ctas');

    const response = await fetch('/process', { method: 'POST' });
    const result = await response.json();
    if (result.zip_path) {
        document.getElementById('status').innerHTML = `<a href="/download/${result.zip_path}" download>Download Processed Videos</a>`;
    } else {
        document.getElementById('status').innerText = 'Error processing videos';
    }
});
