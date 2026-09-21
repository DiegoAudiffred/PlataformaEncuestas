/*
 * JS de editarEncuesta.
 *
 * Antes este código vivía embebido en el template y construía el HTML de
 * cada tarjeta de pregunta con dos plantillas de string distintas (una para
 * "crear" y otra para "editar"), lo que se desincronizaba fácilmente del
 * partial que Django renderiza en el GET inicial.
 *
 * Ahora hay una sola función `PreguntaList.buildCardHtml` que se usa tanto
 * para insertar una pregunta nueva como para refrescar una editada, y su
 * estructura debe reflejar exactamente `_pregunta_card.html`.
 */

(function () {
    'use strict';

    const CONFIG = window.ENCUESTA_CONFIG || {};

    function csrfHeaders() {
        return { 'X-Requested-With': 'XMLHttpRequest' };
    }

    function postForm(formData) {
        return fetch(CONFIG.postUrl || '', {
            method: 'POST',
            body: formData,
            headers: csrfHeaders(),
        }).then(async (res) => {
            const data = await res.json().catch(() => ({}));
            return { ok: res.ok, status: res.status, data };
        });
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.innerText = str == null ? '' : String(str);
        return div.innerHTML;
    }

    // ==================================================================
    // FORMULARIO DE PREGUNTA (crear / editar)
    // ==================================================================
    const EncuestaForm = {

        els: {},

        init() {
            this.els.form = document.getElementById('form-pregunta');
            this.els.selectTipo = document.getElementById('id_tipo');
            this.els.seccionOpciones = document.getElementById('seccion-opciones');
            this.els.seccionUsuarios = document.getElementById('seccion-usuarios');
            this.els.contenedorOpciones = document.getElementById('contenedor-opciones');
            this.els.contenedorUsuarios = document.getElementById('contenedor-usuarios');
            this.els.imgInput = document.getElementById('id_imagen');
            this.els.imgPreview = document.getElementById('question-preview');
            this.els.preguntaId = document.getElementById('pregunta_id');
            this.els.formTitle = document.getElementById('form-title');
            this.els.btnSubmit = document.getElementById('btn-submit-form');
            this.els.btnCancel = document.getElementById('btn-cancel-edit');

            if (!this.els.form) return;

            this.els.selectTipo.addEventListener('change', () => this.toggleSeccion());
            this.els.form.addEventListener('submit', (e) => this.handleSubmit(e));

            if (this.els.imgInput) {
                this.els.imgInput.addEventListener('change', (e) => this.previewImage(e));
            }

            this.toggleSeccion();
            if (this.els.contenedorOpciones.children.length === 0) {
                this.addOptionInput();
            }
        },

        toggleSeccion() {
            const tipo = this.els.selectTipo.value;
            const esUsuario = tipo === 'USUARIO_UNICO' || tipo === 'USUARIO_MULTIPLE';
            const esOpciones = tipo === 'OPCION_MULTIPLE';

            this.els.seccionOpciones.style.display = esOpciones ? 'block' : 'none';
            this.els.seccionUsuarios.classList.toggle('d-none', !esUsuario);
        },

        previewImage(e) {
            const [file] = e.target.files;
            if (!file) return;
            this.els.imgPreview.src = URL.createObjectURL(file);
            this.els.imgPreview.classList.remove('d-none');
        },

        reindexOptions() {
            const rows = this.els.contenedorOpciones.querySelectorAll('.option-row');
            rows.forEach((row, index) => {
                row.setAttribute('data-index', index);
                const checkbox = row.querySelector('input[type="checkbox"]');
                const textInput = row.querySelector('input[name="opciones[]"]');
                checkbox.value = index;
                if (textInput) textInput.placeholder = `Opción ${index + 1}`;
            });
        },

        addOptionInput(texto = '', puntos = 0, esCorrecta = false, opcionId = '') {
            const count = this.els.contenedorOpciones.children.length;
            const div = document.createElement('div');
            div.className = 'input-group mb-2 option-row';
            div.setAttribute('data-index', count);

            div.innerHTML = `
                <input type="hidden" name="opcion_id[]" value="${escapeHtml(opcionId)}">
                <div class="input-group-text">
                    <input class="form-check-input mt-0" type="checkbox" name="es_correcta[]"
                        value="${count}" ${esCorrecta ? 'checked' : ''} title="¿Es correcta?">
                </div>
                <input type="text" name="opciones[]" class="form-control"
                    placeholder="Opción ${count + 1}" value="${escapeHtml(texto)}">
                <input type="number" name="puntos[]" class="form-control" style="max-width: 90px;"
                    placeholder="Pts" value="${escapeHtml(puntos)}">
                <button type="button" class="btn btn-outline-danger remove-option">X</button>
            `;

            div.querySelector('.remove-option').addEventListener('click', () => this.removeOption(div));
            this.els.contenedorOpciones.appendChild(div);
        },

        removeOption(row) {
            if (this.els.contenedorOpciones.children.length > 1) {
                row.remove();
                this.reindexOptions();
            }
        },

        resetToCreate() {
            this.els.form.reset();
            this.els.preguntaId.value = '';
            this.els.formTitle.innerText = `Agregar Pregunta a ${CONFIG.tituloBase || ''}`;
            this.els.btnSubmit.innerText = 'Guardar Pregunta';
            this.els.btnCancel.classList.add('d-none');
            this.els.imgPreview.src = '#';
            this.els.imgPreview.classList.add('d-none');
            this.els.contenedorOpciones.innerHTML = '';
            this.addOptionInput();
            this.els.contenedorUsuarios.querySelectorAll('.usuario-opcion-input').forEach((c) => {
                c.checked = false;
            });
            this.toggleSeccion();
        },

        cargarEdicion(id) {
            const card = document.getElementById(`pregunta-card-${id}`);
            if (!card) return;

            const texto = card.getAttribute('data-texto');
            const tipo = card.getAttribute('data-tipo');
            const imagenUrl = card.getAttribute('data-imagen');

            this.els.preguntaId.value = id;
            document.getElementById('id_texto_pregunta').value = texto;
            this.els.selectTipo.value = tipo;

            this.els.formTitle.innerText = 'Editar Pregunta';
            this.els.btnSubmit.innerText = 'Actualizar Pregunta';
            this.els.btnCancel.classList.remove('d-none');

            if (imagenUrl) {
                this.els.imgPreview.src = imagenUrl;
                this.els.imgPreview.classList.remove('d-none');
            } else {
                this.els.imgPreview.src = '#';
                this.els.imgPreview.classList.add('d-none');
            }

            // Opciones de texto
            this.els.contenedorOpciones.innerHTML = '';
            const opcionesItems = card.querySelectorAll('.option-data-item');
            if (opcionesItems.length > 0) {
                opcionesItems.forEach((item) => {
                    this.addOptionInput(
                        item.getAttribute('data-texto'),
                        item.getAttribute('data-puntos'),
                        item.getAttribute('data-correcta') === 'true',
                        item.getAttribute('data-id')
                    );
                });
            } else {
                this.addOptionInput();
            }

            // Usuarios seleccionados
            const usuarioIds = Array.from(card.querySelectorAll('.usuario-data-item'))
                .map((li) => li.getAttribute('data-id'));

            this.els.contenedorUsuarios.querySelectorAll('.usuario-opcion-input').forEach((c) => {
                c.checked = usuarioIds.includes(c.value);
            });

            this.toggleSeccion();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        handleSubmit(e) {
            e.preventDefault();
            const formData = new FormData(this.els.form);

            postForm(formData).then(({ ok, data }) => {
                if (!ok || data.status !== 'success') {
                    alert('Error al procesar la pregunta: ' + JSON.stringify(data.errors || data.message || data));
                    return;
                }
                PreguntaList.upsertCard(data.pregunta);
                this.resetToCreate();
            }).catch((err) => console.error('Error guardando pregunta:', err));
        },
    };

    // ==================================================================
    // LISTA DE PREGUNTAS (borrar / insertar-actualizar tarjetas)
    // ==================================================================
    const PreguntaList = {

        buildCardHtml(p) {
            const opcionesHtml = (p.opciones || []).map((op) => {
                if (op.es_correcta === undefined) {
                    // usuario "opción" (no tiene puntos/correcta)
                    return `
                        <li class="list-group-item py-1 text-muted usuario-data-item" data-id="${op.id}">
                            👤 ${escapeHtml(op.texto)}
                        </li>`;
                }
                const label = op.es_correcta
                    ? `<strong class="text-success">✓ ${escapeHtml(op.texto)}</strong>`
                    : `• ${escapeHtml(op.texto)}`;
                return `
                    <li class="list-group-item py-1 d-flex justify-content-between align-items-center text-muted option-data-item"
                        data-id="${op.id}" data-texto="${escapeHtml(op.texto)}"
                        data-puntos="${op.puntos}" data-correcta="${op.es_correcta}">
                        <span>${label}</span>
                        <span class="badge bg-secondary rounded-pill">+${op.puntos} pts</span>
                    </li>`;
            }).join('');

            const usuariosHtml = (p.usuarios_opciones || []).map((u) => `
                <li class="list-group-item py-1 text-muted usuario-data-item" data-id="${u.id}">
                    👤 ${escapeHtml(u.nombre)}
                </li>`).join('');

            const imgVisible = p.imagen_url ? '' : 'd-none';
            const imgSrc = p.imagen_url || '';

            return `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-1" id="title-text-${p.id}">${escapeHtml(p.texto)}</h5>
                        <div>
                            <span class="badge bg-info text-dark" id="badge-tipo-${p.id}">${escapeHtml(p.tipo)}</span>
                            <button class="btn btn-sm btn-outline-primary ms-2" onclick="EncuestaForm.cargarEdicion('${p.id}')">Editar</button>
                            <button class="btn btn-sm btn-outline-danger ms-1" onclick="PreguntaList.eliminar('${p.id}')">X</button>
                        </div>
                    </div>
                    <div id="container-img-${p.id}" class="my-2 ${imgVisible}">
                        <img src="${imgSrc}" class="rounded border" style="max-height:100px;object-fit:cover;" id="img-${p.id}">
                    </div>
                    <ul class="list-group list-group-flush mt-2" id="opciones-list-${p.id}">${opcionesHtml}</ul>
                    <ul class="list-group list-group-flush mt-2" id="usuarios-list-${p.id}">${usuariosHtml}</ul>
                </div>`;
        },

        upsertCard(pregunta) {
            const emptyMessage = document.getElementById('empty-message');
            if (emptyMessage) emptyMessage.remove();

            const lista = document.getElementById('lista-preguntas');
            let card = document.getElementById(`pregunta-card-${pregunta.id}`);

            if (!card) {
                card = document.createElement('div');
                card.className = 'card mb-3 shadow-sm';
                card.id = `pregunta-card-${pregunta.id}`;
                lista.appendChild(card);
            }

            card.setAttribute('data-tipo', pregunta.tipo_val);
            card.setAttribute('data-texto', pregunta.texto);
            card.setAttribute('data-imagen', pregunta.imagen_url || '');
            card.innerHTML = this.buildCardHtml(pregunta);
        },

        eliminar(id, force) {
            if (!force && !confirm('¿Deseas eliminar esta pregunta?')) return;

            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', CONFIG.csrfToken);
            formData.append('action', 'delete');
            formData.append('pregunta_id', id);
            if (force) formData.append('force', '1');

            postForm(formData).then(({ status, data }) => {
                if (status === 409 && data.status === 'confirm_required') {
                    if (confirm(data.message + '\n\n¿Eliminar de todas formas?')) {
                        this.eliminar(id, true);
                    }
                    return;
                }

                if (data.status !== 'success') {
                    alert('No se pudo eliminar la pregunta.');
                    return;
                }

                const card = document.getElementById(`pregunta-card-${id}`);
                if (card) card.remove();

                const lista = document.getElementById('lista-preguntas');
                if (lista.children.length === 0) {
                    lista.innerHTML = '<p class="text-center text-muted" id="empty-message">No hay preguntas creadas aún.</p>';
                }
            }).catch((err) => console.error('Error eliminando pregunta:', err));
        },
    };

    // ==================================================================
    // MODAL EDITAR ENCUESTA
    // ==================================================================
    function initEditarEncuestaModal() {
        const form = document.getElementById('form-editar-encuesta');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);

            postForm(formData).then(({ data }) => {
                if (data.status !== 'success') {
                    alert('Error al actualizar la encuesta: ' + JSON.stringify(data.errors));
                    return;
                }

                document.getElementById('titulo-encuesta').innerText = data.encuesta.titulo;
                document.getElementById('descripcion-encuesta').innerText = data.encuesta.descripcion;

                const nuevoTitulo = `Agregar Pregunta a ${data.encuesta.titulo}`;
                document.getElementById('form-title').innerText = nuevoTitulo;
                CONFIG.tituloBase = data.encuesta.titulo;

                const modalElement = document.getElementById('modal-editar-encuesta');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) modal.hide();
            }).catch((err) => console.error('Error actualizando encuesta:', err));
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        EncuestaForm.init();
        initEditarEncuestaModal();
    });

    // Exponer para los onclick inline de los partials
    window.EncuestaForm = EncuestaForm;
    window.PreguntaList = PreguntaList;
})();