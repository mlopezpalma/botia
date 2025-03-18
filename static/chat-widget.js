(function() {
    // Crear elementos del chat
    var chatDiv = document.createElement('div');
    chatDiv.id = 'bot-chat-container';
    chatDiv.style.position = 'fixed';
    chatDiv.style.bottom = '20px';
    chatDiv.style.right = '20px';
    chatDiv.style.width = '350px';
    chatDiv.style.height = '500px';
    chatDiv.style.border = '1px solid #ccc';
    chatDiv.style.borderRadius = '10px';
    chatDiv.style.backgroundColor = '#fff';
    chatDiv.style.boxShadow = '0 0 10px rgba(0,0,0,0.1)';
    chatDiv.style.display = 'flex';
    chatDiv.style.flexDirection = 'column';
    chatDiv.style.overflow = 'hidden';
    chatDiv.style.zIndex = '1000';
    chatDiv.style.transition = 'all 0.3s ease';
    
    // Crear el botón minimizado
    var chatButton = document.createElement('div');
    chatButton.id = 'bot-chat-button';
    chatButton.style.position = 'fixed';
    chatButton.style.bottom = '20px';
    chatButton.style.right = '20px';
    chatButton.style.width = '60px';
    chatButton.style.height = '60px';
    chatButton.style.borderRadius = '50%';
    chatButton.style.backgroundColor = '#1890ff';
    chatButton.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    chatButton.style.cursor = 'pointer';
    chatButton.style.zIndex = '999';
    chatButton.style.display = 'flex';
    chatButton.style.justifyContent = 'center';
    chatButton.style.alignItems = 'center';
    chatButton.style.transition = 'all 0.3s ease';
    
    // Ícono del botón
    chatButton.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    
    // Cabecera
    var header = document.createElement('div');
    header.style.padding = '15px';
    header.style.backgroundColor = '#2c3e50';
    header.style.color = 'white';
    header.style.fontWeight = 'bold';
    header.style.borderTopLeftRadius = '10px';
    header.style.borderTopRightRadius = '10px';
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';
    
    var headerTitle = document.createElement('div');
    headerTitle.textContent = 'Asistente de Citas Legales';
    
    var minimizeButton = document.createElement('div');
    minimizeButton.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    minimizeButton.style.cursor = 'pointer';
    
    header.appendChild(headerTitle);
    header.appendChild(minimizeButton);
    
    // Área de mensajes
    var messagesArea = document.createElement('div');
    messagesArea.id = 'bot-messages';
    messagesArea.style.flex = '1';
    messagesArea.style.padding = '15px';
    messagesArea.style.overflowY = 'auto';
    
    // Área de entrada
    var inputArea = document.createElement('div');
    inputArea.style.borderTop = '1px solid #e0e0e0';
    inputArea.style.padding = '10px';
    inputArea.style.display = 'flex';
    
    var inputBox = document.createElement('input');
    inputBox.id = 'bot-input';
    inputBox.type = 'text';
    inputBox.style.flex = '1';
    inputBox.style.padding = '8px';
    inputBox.style.border = '1px solid #ddd';
    inputBox.style.borderRadius = '4px';
    inputBox.style.marginRight = '10px';
    inputBox.placeholder = 'Escribe tu mensaje aquí...';
    
    var sendButton = document.createElement('button');
    sendButton.textContent = 'Enviar';
    sendButton.style.padding = '8px 15px';
    sendButton.style.backgroundColor = '#1890ff';
    sendButton.style.color = 'white';
    sendButton.style.border = 'none';
    sendButton.style.borderRadius = '4px';
    sendButton.style.cursor = 'pointer';
    sendButton.style.transition = 'background-color 0.3s ease';
    
    sendButton.addEventListener('mouseover', function() {
        this.style.backgroundColor = '#40a9ff';
    });
    
    sendButton.addEventListener('mouseout', function() {
        this.style.backgroundColor = '#1890ff';
    });
    
    // Botón de calendario (inicialmente oculto)
    var calendarButton = document.createElement('button');
    calendarButton.id = 'calendar-button';
    calendarButton.textContent = 'Ver Calendario';
    calendarButton.style.display = 'none'; // Inicialmente oculto
    calendarButton.style.padding = '8px 15px';
    calendarButton.style.backgroundColor = '#52c41a';
    calendarButton.style.color = 'white';
    calendarButton.style.border = 'none';
    calendarButton.style.borderRadius = '4px';
    calendarButton.style.marginTop = '10px';
    calendarButton.style.cursor = 'pointer';
    
    // Div para el calendario (inicialmente oculto)
    var calendarDiv = document.createElement('div');
    calendarDiv.id = 'chat-calendar';
    calendarDiv.style.display = 'none';
    calendarDiv.style.padding = '10px';
    calendarDiv.style.backgroundColor = '#f9f9f9';
    calendarDiv.style.border = '1px solid #ddd';
    calendarDiv.style.borderRadius = '4px';
    calendarDiv.style.marginTop = '10px';
    
    // Añadir elementos al DOM
    inputArea.appendChild(inputBox);
    inputArea.appendChild(sendButton);
    
    chatDiv.appendChild(header);
    chatDiv.appendChild(messagesArea);
    chatDiv.appendChild(calendarButton);
    chatDiv.appendChild(calendarDiv);
    chatDiv.appendChild(inputArea);
    
    document.body.appendChild(chatButton);
    document.body.appendChild(chatDiv);
    
    // Inicialmente, mostrar solo el botón y esconder el chat
    chatDiv.style.display = 'none';
    
    // Generar ID único para el usuario
    var userId = 'user_' + Math.random().toString(36).substr(2, 9);
    var chatActive = false; // Para rastrear si el chat está activo o no
    
    // Evento para mostrar/ocultar el chat
    chatButton.addEventListener('click', function() {
        chatDiv.style.display = 'flex';
        chatButton.style.display = 'none';
        
        // Si es la primera vez que se abre o se había cerrado anteriormente
        if (!chatActive) {
            // Limpiar mensajes anteriores
            messagesArea.innerHTML = '';
            
            // Reiniciar la conversación con el backend
            fetch('/api/bot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mensaje: "reset_conversation",
                    user_id: userId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Mostrar mensaje de bienvenida
                addBotMessage('¡Hola! Soy el asistente de citas legales. ¿En qué puedo ayudarte hoy?');
                chatActive = true;
            })
            .catch(error => {
                console.error('Error:', error);
                addBotMessage('Lo siento, ha ocurrido un error al iniciar la conversación.');
                chatActive = true;
            });
        }
    });
    
    // Evento para minimizar el chat
    minimizeButton.addEventListener('click', function() {
        chatDiv.style.display = 'none';
        chatButton.style.display = 'flex';
        // Marcar el chat como cerrado
        chatActive = false;
    });
    
    // Evento de envío de mensaje
    function sendMessage() {
        var message = inputBox.value.trim();
        if (message) {
            addUserMessage(message);
            
            // Ocultar el calendario si está visible
            calendarDiv.style.display = 'none';
            
            // Enviar mensaje al servidor
            fetch('/api/bot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mensaje: message,
                    user_id: userId
                })
            })
            .then(response => response.json())
            .then(data => {
                addBotMessage(data.respuesta);
                
                // Mostrar el botón de calendario si la respuesta lo menciona
                if (data.respuesta.includes('[Indicador pequeño]')) {
                    calendarButton.style.display = 'inline-block';
                } else {
                    calendarButton.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addBotMessage('Lo siento, ha ocurrido un error al procesar tu mensaje.');
            });
            
            inputBox.value = '';
        }
    }
    
    // Función para mostrar el calendario
    calendarButton.addEventListener('click', function() {
        if (calendarDiv.style.display === 'none') {
            // Verificar si se ha seleccionado un tipo de reunión
            var tipoReunion = getTipoReunion();
            if (!tipoReunion) {
                addBotMessage("Por favor, primero selecciona un tipo de reunión (presencial, videoconferencia o telefónica).");
                return;
            }
            
            // Generar un calendario con los días disponibles
            var today = new Date();
            var calendarHTML = generateCalendar(today);
            calendarDiv.innerHTML = calendarHTML;
            calendarDiv.style.display = 'block';
            
            // Añadir eventos a las fechas
            var dateCells = calendarDiv.querySelectorAll('.date-cell');
            dateCells.forEach(function(cell) {
                cell.addEventListener('click', function() {
                    var date = this.getAttribute('data-date');
                    inputBox.value = 'Quiero una cita el ' + date;
                    calendarDiv.style.display = 'none';
                    sendMessage();
                });
            });
            
            // Añadir eventos a los botones de navegación
            var prevMonthButton = calendarDiv.querySelector('#prev-month');
            var nextMonthButton = calendarDiv.querySelector('#next-month');
            
            prevMonthButton.addEventListener('click', function() {
                var currentMonth = today.getMonth();
                today.setMonth(currentMonth - 1);
                calendarDiv.innerHTML = generateCalendar(today);
                
                // Volver a añadir eventos a las fechas y botones
                dateCells = calendarDiv.querySelectorAll('.date-cell');
                dateCells.forEach(function(cell) {
                    cell.addEventListener('click', function() {
                        var date = this.getAttribute('data-date');
                        inputBox.value = 'Quiero una cita el ' + date;
                        calendarDiv.style.display = 'none';
                        sendMessage();
                    });
                });
                
                // Volver a añadir eventos a los botones de navegación
                prevMonthButton = calendarDiv.querySelector('#prev-month');
                nextMonthButton = calendarDiv.querySelector('#next-month');
                
                prevMonthButton.addEventListener('click', function() {
                    today.setMonth(today.getMonth() - 1);
                    calendarDiv.innerHTML = generateCalendar(today);
                });
                
                nextMonthButton.addEventListener('click', function() {
                    today.setMonth(today.getMonth() + 1);
                    calendarDiv.innerHTML = generateCalendar(today);
                });
            });
            
            nextMonthButton.addEventListener('click', function() {
                var currentMonth = today.getMonth();
                today.setMonth(currentMonth + 1);
                calendarDiv.innerHTML = generateCalendar(today);
            
                // Volver a añadir eventos a las fechas y botones
                dateCells = calendarDiv.querySelectorAll('.date-cell');
                dateCells.forEach(function(cell) {
                    cell.addEventListener('click', function() {
                        var date = this.getAttribute('data-date');
                        inputBox.value = 'Quiero una cita el ' + date;
                        calendarDiv.style.display = 'none';
                        sendMessage();
                    });
                });
                
                // Volver a añadir eventos a los botones de navegación
                prevMonthButton = calendarDiv.querySelector('#prev-month');
                nextMonthButton = calendarDiv.querySelector('#next-month');
                
                prevMonthButton.addEventListener('click', arguments.callee);
                nextMonthButton.addEventListener('click', arguments.callee);
            });
        } else {
            calendarDiv.style.display = 'none';
        }
    });
    






    
    // Generar HTML del calendario
    function generateCalendar(date) {
        var year = date.getFullYear();
        var month = date.getMonth();
        
        var firstDay = new Date(year, month, 1);
        var lastDay = new Date(year, month + 1, 0);
        
        var monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        
        var html = '<div style="text-align:center; margin-bottom:10px;"><strong>' + monthNames[month] + ' ' + year + '</strong></div>';
        
        // Añadir botones para navegar entre meses
        html += '<div style="display:flex; justify-content:space-between; margin-bottom:10px;">';
        html += '<button id="prev-month" style="padding:5px 10px; background-color:#f0f0f0; border:1px solid #ccc; cursor:pointer;">&lt; Anterior</button>';
        html += '<button id="next-month" style="padding:5px 10px; background-color:#f0f0f0; border:1px solid #ccc; cursor:pointer;">Siguiente &gt;</button>';
        html += '</div>';
        
        // Mostrar el tipo de reunión seleccionado
        var tipoReunion = getTipoReunion();
        if (tipoReunion) {
            html += '<div style="text-align:center; margin-bottom:10px;"><small>Mostrando disponibilidad para: <strong>' + tipoReunion + '</strong></small></div>';
        } else {
            html += '<div style="text-align:center; margin-bottom:10px;"><small>Primero selecciona un tipo de reunión para ver la disponibilidad</small></div>';
        }
        
        html += '<table style="width:100%; border-collapse:collapse;">';
        html += '<tr>';
        ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].forEach(function(day) {
            html += '<th style="padding:5px; text-align:center; font-size:12px;">' + day + '</th>';
        });
        html += '</tr>';
        
        // Obtener días disponibles para el mes actual
        var diasDisponibles = [];
        if (tipoReunion) {
            diasDisponibles = obtenerDiasDisponibles(month + 1, year, tipoReunion);
        }
        
        // Ajustar el primer día (0 = Domingo, 1 = Lunes, ..., 6 = Sábado)
        var firstDayOfWeek = firstDay.getDay();
        if (firstDayOfWeek === 0) firstDayOfWeek = 7; // Ajustar domingo a 7 para que la semana comience en lunes (1)
        
        var currentDate = new Date(firstDay);
        currentDate.setDate(currentDate.getDate() - firstDayOfWeek + 1);
        
        // Generar filas del calendario
        for (var i = 0; i < 6; i++) {
            html += '<tr>';
            for (var j = 0; j < 7; j++) {
                var dayClass = '';
                var isEnabled = false;
                
                // Verificar si es un día del mes actual
                var isDifferentMonth = currentDate.getMonth() !== month;
                if (isDifferentMonth) {
                    dayClass = 'other-month';
                }
                
                // Verificar si es hoy
                if (currentDate.toDateString() === new Date().toDateString()) {
                    dayClass += ' today';
                }
                
                // Verificar si es fin de semana
                var isWeekend = currentDate.getDay() === 0 || currentDate.getDay() === 6;
                if (isWeekend) {
                    dayClass += ' weekend';
                }
                
                // Verificar si es un día pasado
                var isPastDay = currentDate < new Date().setHours(0, 0, 0, 0);
                if (isPastDay) {
                    dayClass += ' past';
                }
                
                // Verificar si es un día con disponibilidad
                var dayOfMonth = currentDate.getDate();
                var isAvailable = !isDifferentMonth && !isWeekend && !isPastDay && 
                                  diasDisponibles.indexOf(dayOfMonth) !== -1;
                
                if (isAvailable) {
                    isEnabled = true;
                    dayClass += ' available';
                }
                
                var dateStr = currentDate.getDate() + '/' + (currentDate.getMonth() + 1) + '/' + currentDate.getFullYear();
                
                if (isEnabled) {
                    html += '<td class="date-cell ' + dayClass + '" data-date="' + dateStr + '" style="padding:5px; text-align:center; cursor:pointer; border:1px solid #eee; font-size:14px; background-color:#d0f0d0;">' + currentDate.getDate() + '</td>';
                } else {
                    html += '<td class="' + dayClass + '" style="padding:5px; text-align:center; color:#ccc; border:1px solid #eee; font-size:14px; background-color:' + (isDifferentMonth ? '#f9f9f9' : '#f0f0f0') + ';">' + currentDate.getDate() + '</td>';
                }
                
                currentDate.setDate(currentDate.getDate() + 1);
            }
            html += '</tr>';
            
            // Detener si ya hemos pasado al siguiente mes
            if (currentDate.getMonth() !== month && j === 0) {
                break;
            }
        }
        
        html += '</table>';
        
        // Añadir leyenda
        html += '<div style="margin-top:10px; font-size:12px;">';
        html += '<div style="display:inline-block; width:12px; height:12px; background-color:#d0f0d0; margin-right:5px;"></div> Días con disponibilidad';
        html += '</div>';
        
        return html;
    }

// Función para obtener el tipo de reunión seleccionado por el usuario
function getTipoReunion() {
    // Intentar obtener el tipo de reunión del último mensaje enviado
    var messagesArea = document.getElementById('bot-messages');
    if (!messagesArea) return null;
    
    var messages = messagesArea.getElementsByClassName('bot-message');
    if (!messages || messages.length === 0) return null;
    
    // Buscar en los mensajes recientes menciones a tipos de reunión
    var tipos = ['presencial', 'videoconferencia', 'telefonica', 'telefónica'];
    var tipoSeleccionado = null;
    
    // Comprobar los últimos 5 mensajes o menos
    var numMessages = Math.min(5, messages.length);
    for (var i = messages.length - 1; i >= messages.length - numMessages; i--) {
        var messageText = messages[i].innerText.toLowerCase();
        
        for (var j = 0; j < tipos.length; j++) {
            if (messageText.indexOf(tipos[j]) !== -1) {
                tipoSeleccionado = tipos[j];
                break;
            }
        }
        
        if (tipoSeleccionado) break;
    }
    
    return tipoSeleccionado;
}

// Función para simular obtención de días disponibles
function obtenerDiasDisponibles(mes, anio, tipoReunion) {
    // En una implementación real, esto sería una llamada a un endpoint del servidor
    console.log('Obteniendo días disponibles para', mes, anio, tipoReunion);
    
    // Simulación: Días entre semana, excluyendo aleatoriamente algunos días
    var diasLaborables = [];
    var diasTotales = new Date(anio, mes, 0).getDate();
    
    for (var dia = 1; dia <= diasTotales; dia++) {
        var fecha = new Date(anio, mes - 1, dia);
        var diaSemana = fecha.getDay();
        
        // Excluir fines de semana (0 = Domingo, 6 = Sábado)
        if (diaSemana !== 0 && diaSemana !== 6) {
            // Excluir días pasados
            var hoy = new Date();
            if (fecha >= new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate()) || 
                (fecha.getFullYear() === hoy.getFullYear() && fecha.getMonth() === hoy.getMonth() && fecha.getDate() === hoy.getDate())) {
                diasLaborables.push(dia);
            }
        }
    }
    
    // Excluir aleatoriamente algunos días (simulando días sin disponibilidad)
    var diasExcluidos = Math.floor(diasLaborables.length * 0.3); // Excluir aproximadamente 30%
    for (var i = 0; i < diasExcluidos; i++) {
        var indexAleatorio = Math.floor(Math.random() * diasLaborables.length);
        diasLaborables.splice(indexAleatorio, 1);
    }
    
    return diasLaborables;
}







    // Funciones para añadir mensajes
    function addUserMessage(text) {
        var messageDiv = document.createElement('div');
        messageDiv.style.textAlign = 'right';
        messageDiv.style.marginBottom = '10px';
        
        var messageBubble = document.createElement('div');
        messageBubble.style.display = 'inline-block';
        messageBubble.style.maxWidth = '70%';
        messageBubble.style.padding = '8px 12px';
        messageBubble.style.backgroundColor = '#e6f7ff';
        messageBubble.style.borderRadius = '15px';
        messageBubble.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
        messageBubble.textContent = text;
        
        messageDiv.appendChild(messageBubble);
        messagesArea.appendChild(messageDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
    
    function addBotMessage(text) {
        var messageDiv = document.createElement('div');
        messageDiv.style.textAlign = 'left';
        messageDiv.style.marginBottom = '10px';
        
        var messageBubble = document.createElement('div');
        messageBubble.style.display = 'inline-block';
        messageBubble.style.maxWidth = '70%';
        messageBubble.style.padding = '8px 12px';
        messageBubble.style.backgroundColor = '#f0f0f0';
        messageBubble.style.borderRadius = '15px';
        messageBubble.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
        
        // Filtrar indicador pequeño
        text = text.replace('[Indicador pequeño]', '');
        
        // Buscar opciones de menú en el formato [MENU:opción1|opción2|opción3]
        var menuMatch = text.match(/\[MENU:(.*?)\]/);
        if (menuMatch) {
            var menuText = text.replace(menuMatch[0], '');
            var options = menuMatch[1].split('|');
            
            // Preservar saltos de línea para el texto principal
            menuText.split('\\n').forEach((line, index, array) => {
                messageBubble.appendChild(document.createTextNode(line));
                if (index < array.length - 1) {
                    messageBubble.appendChild(document.createElement('br'));
                }
            });
            
            messageDiv.appendChild(messageBubble);
            
            // Crear un contenedor para los botones del menú
            var menuContainer = document.createElement('div');
            menuContainer.style.marginTop = '10px';
            menuContainer.style.display = 'flex';
            menuContainer.style.flexDirection = 'column';
            menuContainer.style.alignItems = 'flex-start';
            menuContainer.style.gap = '5px';
            
            // Crear botones para cada opción
            options.forEach(function(option) {
                var optionButton = document.createElement('button');
                optionButton.textContent = option;
                optionButton.style.padding = '8px 12px';
                optionButton.style.backgroundColor = '#e8f4ff';
                optionButton.style.color = '#0366d6';
                optionButton.style.border = '1px solid #0366d6';
                optionButton.style.borderRadius = '15px';
                optionButton.style.cursor = 'pointer';
                optionButton.style.fontSize = '14px';
                optionButton.style.margin = '2px 0';
                optionButton.style.transition = 'all 0.2s ease';
                
                optionButton.addEventListener('mouseover', function() {
                    this.style.backgroundColor = '#0366d6';
                    this.style.color = 'white';
                });
                
                optionButton.addEventListener('mouseout', function() {
                    this.style.backgroundColor = '#e8f4ff';
                    this.style.color = '#0366d6';
                });
                
                optionButton.addEventListener('click', function() {
                    // Eliminar los botones de opciones después de hacer clic
                    menuContainer.remove();
                    
                    // Enviar la opción seleccionada
                    inputBox.value = option;
                    sendMessage();
                });
                
                menuContainer.appendChild(optionButton);
            });
            
            messageDiv.appendChild(menuContainer);
        } else {
            // Preservar saltos de línea para el texto normal
            text.split('\\n').forEach((line, index, array) => {
                messageBubble.appendChild(document.createTextNode(line));
                if (index < array.length - 1) {
                    messageBubble.appendChild(document.createElement('br'));
                }
            });
            
            messageDiv.appendChild(messageBubble);
        }
        
        messagesArea.appendChild(messageDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
})();
