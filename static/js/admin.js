/* Legado: preferível carregar /static/js/phd-ui.js antes deste script. */
function _phdMsg(msg, type) {
    if (window.phdUI) phdUI.toast(msg, type || "info");
    else alert(msg);
}

async function gerarGrade() {
    const data = document.getElementById('grade-data').value;
    const inicio = document.getElementById('grade-inicio').value;
    const fim = document.getElementById('grade-fim').value;
    const intervalo = parseInt(document.getElementById('grade-intervalo').value);
    const token = localStorage.getItem('token_phd');

    if (!data) {
        _phdMsg("Selecione a data!", "warning");
        return;
    }

    const res = await fetch(`${API_URL}/admin/gerar-grade`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ data, inicio, fim, intervalo })
    });

    if (res.ok) {
        _phdMsg("Grade gerada com sucesso!", "success");
        carregarAgendamentos();
    } else {
        _phdMsg("Erro ao gerar grade.", "error");
    }
}
