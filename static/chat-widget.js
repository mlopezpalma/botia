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
    
    // Área para el calendario (inicialmente oculto)
    var calendarButton = document.createElement('button');
    calendarButton.id = 'calendar-button';
    calendarButton.textContent = 'Ver Calendario';
    calendarButton.style.display = 'none';
    calendarButton.style.padding = '8px 15px';
    calendarButton.style.backgroundColor = '#52c41a';
    calendarButton.style.color = 'white';
    calendarButton.style.border = 'none';
    calendarButton.style.borderRadius = '4px';
    calendarButton.style.marginTop = '10px';
    calendarButton.style.cursor = 'pointer';
    
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
        
        // Eliminar indicadores especiales
        text = text.replace('[Indicador pequeño]', '');
        
        // Buscar opciones de menú en el formato [MENU:opción1|opción2|opción3]
        var menuMatch = text.match(/\[MENU:(.*?)\]/);
        if (menuMatch) {
            var menuText = text.replace(menuMatch[0], '');
            var options = menuMatch[1].split('|');
            
            messageBubble.textContent = menuText;
            messageDiv.appendChild(messageBubble);
            
            // Crear botones para cada opción
            var menuContainer = document.createElement('div');
            menuContainer.style.marginTop = '10px';
            menuContainer.style.display = 'flex';
            menuContainer.style.flexDirection = 'column';
            menuContainer.style.alignItems = 'flex-start';
            
            options.forEach(function(option) {
                var optionButton = document.createElement('button');
                optionButton.textContent = option;
                optionButton.style.margin = '5px 0';
                optionButton.style.padding = '8px';
                optionButton.style.backgroundColor = '#e8f4ff';
                optionButton.style.color = '#0366d6';
                optionButton.style.border = '1px solid #0366d6';
                optionButton.style.borderRadius = '15px';
                optionButton.style.cursor = 'pointer';
                
                optionButton.onclick = function() {
                    sendUserMessage(option);
                };
                
                menuContainer.appendChild(optionButton);
            });
            
            messageDiv.appendChild(menuContainer);
        } else {
            messageBubble.textContent = text;
            messageDiv.appendChild(messageBubble);
        }
        
        messagesArea.appendChild(messageDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
        
        // Mostrar el botón de calendario si la respuesta lo menciona
        if (text.includes('[Indicador pequeño]')) {
            calendarButton.style.display = 'inline-block';
        } else {
            calendarButton.style.display = 'none';
        }
    }
    
    // Función para enviar mensajes
    function sendUserMessage(message) {
        if (message) {
            addUserMessage(message);
            
            // Ocultar el calendario si está visible
            calendarDiv.style.display = 'none';
            
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
            })
            .catch(error => {
                console.error('Error:', error);
                addBotMessage('Lo siento, ha ocurrido un error al procesar tu mensaje.');
            });
            
            inputBox.value = '';
        }
    }
    
    // Evento para mostrar el chat
    chatButton.onclick = function() {
        chatDiv.style.display = 'flex';
        chatButton.style.display = 'none';
        
        // Iniciar conversación
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
        .then(() => {
            // Ahora enviamos un saludo
            fetch('/api/bot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mensaje: "hola",
                    user_id: userId
                })
            })
            .then(response => response.json())
            .then(data => {
                addBotMessage(data.respuesta);
            });
        });
    };
    
    // Evento para minimizar el chat
    minimizeButton.onclick = function() {
        chatDiv.style.display = 'none';
        chatButton.style.display = 'flex';
    };
    
    // Evento para enviar mensaje con el botón
    sendButton.onclick = function() {
        sendUserMessage(inputBox.value.trim());
    };
    
    // Evento para enviar mensaje con Enter
    inputBox.onkeypress = function(e) {
        if (e.key === 'Enter') {
            sendUserMessage(inputBox.value.trim());
        }
    };
    
    // Evento para el botón de calendario
    calendarButton.onclick = function() {
        if (calendarDiv.style.display === 'none') {
            calendarDiv.innerHTML = 'Cargando calendario...';
            calendarDiv.style.display = 'block';
            
            // Simulación de visualización de calendario
            setTimeout(function() {
                var fechaActual = new Date();
                var mes = fechaActual.getMonth();
                var anio = fechaActual.getFullYear();
                var tipo_reunion = 'presencial'; // Por defecto
                
                calendarDiv.innerHTML = generateCalendar(fechaActual, tipo_reunion);
                
                // Añadir eventos a las fechas
                var dateCells = calendarDiv.querySelectorAll('.date-cell');
                dateCells.forEach(function(cell) {
                    cell.addEventListener('click', function() {
                        var date = this.getAttribute('data-date');
                        inputBox.value = 'Quiero una cita el ' + date;
                        sendUserMessage(inputBox.value);
                        calendarDiv.style.display = 'none';
                    });
                });
            }, 500);
        } else {
            calendarDiv.style.display = 'none';
        }
    };
    
    // Función para generar el calendario
    function generateCalendar(date, tipo_reunion) {
        var year = date.getFullYear();
        var month = date.getMonth();
        
        var firstDay = new Date(year, month, 1);
        var lastDay = new Date(year, month + 1, 0);
        
        var monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        
        var html = '<div style="text-align:center; margin-bottom:10px;"><strong>' + monthNames[month] + ' ' + year + '</strong></div>';
        
        html += '<table style="width:100%; border-collapse:collapse;">';
        html += '<tr>';
        ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].forEach(function(day) {
            html += '<th style="padding:5px; text-align:center; font-size:12px;">' + day + '</th>';
        });
        html += '</tr>';
        
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
                
                // Simulación de días disponibles (todos los días entre semana que no son pasados)
                var isAvailable = !isDifferentMonth && !isWeekend && !isPastDay;
                
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
})();