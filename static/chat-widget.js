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
    
    // Evento para mostrar/ocultar el chat
    chatButton.addEventListener('click', function() {
        chatDiv.style.display = 'flex';
        chatButton.style.display = 'none';
        if (messagesArea.children.length === 0) {
            // Mostrar mensaje de bienvenida solo la primera vez
            addBotMessage('¡Hola! Soy el asistente de citas legales. ¿En qué puedo ayudarte hoy?');
        }
    });
    
    // Evento para minimizar el chat
    minimizeButton.addEventListener('click', function() {
        chatDiv.style.display = 'none';
        chatButton.style.display = 'flex';
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
            // Generar un calendario simple
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
                var isEnabled = true;
                
                // Verificar si es un día del mes actual
                if (currentDate.getMonth() !== month) {
                    dayClass = 'other-month';
                    isEnabled = false;
                }
                
                // Verificar si es hoy
                if (currentDate.toDateString() === new Date().toDateString()) {
                    dayClass += ' today';
                }
                
                // Verificar si es fin de semana
                if (currentDate.getDay() === 0 || currentDate.getDay() === 6) {
                    dayClass += ' weekend';
                    isEnabled = false;
                }
                
                // Verificar si es un día pasado
                if (currentDate < new Date().setHours(0, 0, 0, 0)) {
                    dayClass += ' past';
                    isEnabled = false;
                }
                
                var dateStr = currentDate.getDate() + '/' + (currentDate.getMonth() + 1) + '/' + currentDate.getFullYear();
                
                if (isEnabled) {
                    html += '<td class="date-cell ' + dayClass + '" data-date="' + dateStr + '" style="padding:5px; text-align:center; cursor:pointer; border:1px solid #eee; font-size:14px; background-color:#f0f8ff;">' + currentDate.getDate() + '</td>';
                } else {
                    html += '<td class="' + dayClass + '" style="padding:5px; text-align:center; color:#ccc; border:1px solid #eee; font-size:14px;">' + currentDate.getDate() + '</td>';
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
        return html;
    }
    
    // Añadir eventos
    sendButton.addEventListener('click', sendMessage);
    inputBox.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
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
