async function gerarGrade() {
    const data = document.getElementById('grade-data').value;
    const inicio = document.getElementById('grade-inicio').value;
    const fim = document.getElementById('grade-fim').value;
    const intervalo = parseInt(document.getElementById('grade-intervalo').value);
    const token = localStorage.getItem('token_phd');

    if(!data) return alert("Selecione a data!");

    const res = await fetch(`${API_URL}/admin/gerar-grade`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ data, inicio, fim, intervalo })
    });

    if(res.ok) {
        alert("Grade gerada com sucesso!");
        carregarAgendamentos();
    }
}