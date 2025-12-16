document.addEventListener('DOMContentLoaded', () => {
    const delLinks = document.querySelectorAll(".delete");
    delLinks.forEach(l => {
        l.addEventListener('click', (e) => {
            if (!confirm('Are you sure you want to delete this report?')) {
                e.preventDefault();
            } else {
                showToast("🗑 Report deleted");
            }
        });
    });

    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase();
            const patientSections = document.querySelectorAll('.patient-section');
            patientSections.forEach(section => {
                const patientName = section.querySelector('.patient-title').textContent.toLowerCase();
                if (patientName.includes(searchTerm)) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        });
    }
});
