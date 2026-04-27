document.addEventListener('DOMContentLoaded', function () {
    const loadingOverlay = document.getElementById('loadingOverlay');
    const jsonOverlay = document.getElementById('jsonOverlay');
    const jsonContainer = document.getElementById('jsonContainer');
    const closeJson = document.getElementById('closeJson');
    const btn = document.getElementById('btnPesquisar');
    const unlockedBtn = document.getElementById('unlockedBtn');
    const rebootButton = document.getElementById('rebootButton');

    function normalizeAlarm(item) {
        if (item.alarm === 'The dying-gasp of GPON ONTi (DGi) is generated') return 'Falta de energia';
        if (item.alarm?.includes('distribute fiber is broken')) return 'LOS';
        if (item.alarm?.includes('loss of GEM')) return 'LOS';
        return item.alarm;
    }

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            document.getElementById('btnPesquisar').click();
        }
    });

    btn.addEventListener('click', function () {
        const modo = document.querySelector('input[name="modo"]:checked');
        if (!modo) {
            alert('Selecione uma OLT!');
            return;
        }

        const cliente = document.getElementById('cliente').value.trim();
        if (!cliente) {
            alert('Digite o nome do cliente!');
            return;
        }

        loadingOverlay.classList.add('show');

        fetch('/olt/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ olt: modo.value, cliente: cliente })
        })
            .then(res => res.json())
            .then(data => {
                jsonContainer.innerHTML = '';

                if (!Array.isArray(data)) {
                    alert(data?.erro || 'Erro ao consultar OLT.');
                    return;
                }

                if (data.length === 0) {
                    alert('Nenhuma ONU encontrada para este cliente.');
                    return;
                }

                data.forEach(item => {
                    const radio = document.createElement('input');
                    radio.type = 'radio';
                    radio.className = 'btn-check';
                    radio.autocomplete = 'off';
                    radio.id = `${item.olt_ip},${item.fsp} ${item.ont_id}`;
                    radio.name = 'onu';

                    const label = document.createElement('label');
                    label.className = 'btn json-card';
                    label.setAttribute('for', `${item.olt_ip},${item.fsp} ${item.ont_id}`);

                    if (item.run_state === 'online') label.classList.add('online');
                    else if (item.run_state === 'offline') label.classList.add('offline');
                    else label.classList.add('other');

                    item.alarm = normalizeAlarm(item);

                    label.innerHTML = `
                    <p><strong>${item.description}</strong></p>
                    <p><strong>FSP:</strong> ${item.fsp}</p>
                    <p><strong>ONU ID:</strong> ${item.ont_id}</p>
                    <p><strong>Status:</strong> ${item.run_state ?? 'N/A'}</p>
                    <p><strong>RX Power:</strong> ${item.rx_power ?? 'N/A'}</p>
                    <p><strong>Last Down:</strong> ${item.alarm ?? 'N/A'}</p>
                    <p><strong>SN:</strong> ${item.sn ?? 'N/A'}</p>
                `;
                    jsonContainer.appendChild(radio);
                    jsonContainer.appendChild(label);
                });

                jsonOverlay.classList.add('show');
            })
            .catch(() => {
                alert('Erro ao buscar o status da ONU!');
            })
            .finally(() => loadingOverlay.classList.remove('show'));
    });

    closeJson.addEventListener('click', () => {
        jsonOverlay.classList.remove('show');
    });

    unlockedBtn.addEventListener('click', () => {
        const onu = document.querySelector('input[name="onu"]:checked');
        if (!onu) {
            alert('Selecione uma ONU!');
            return;
        }

        loadingOverlay.classList.add('show');
        fetch('/olt/unlocked/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ onu: onu.id })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    alert('Liberacao da ONU realizada.');
                    return;
                }
                alert(`Erro: ${data.mensagem || 'falha ao liberar ONU.'}`);
            })
            .catch(() => {
                alert('Erro de rede ao liberar ONU.');
            })
            .finally(() => loadingOverlay.classList.remove('show'));
    });

    rebootButton.addEventListener('click', () => {
        const onu = document.querySelector('input[name="onu"]:checked');
        if (!onu) {
            alert('Selecione uma ONU!');
            return;
        }

        loadingOverlay.classList.add('show');
        fetch('/olt/reboot/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ onu: onu.id })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    alert('Reboot da ONU realizado.');
                    return;
                }
                alert(`Erro: ${data.mensagem || 'falha ao reiniciar ONU.'}`);
            })
            .catch(() => {
                alert('Erro de rede ao reiniciar ONU.');
            })
            .finally(() => loadingOverlay.classList.remove('show'));
    });
});
