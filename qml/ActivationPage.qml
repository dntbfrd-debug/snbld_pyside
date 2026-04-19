import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Page {
    id: activationPage
    visible: true
    
    // Цвета
    readonly property color accentColor: "#fd79a8"
    readonly property color bgColor: "#1a1a2e"
    readonly property color cardColor: "#0f0f1e"
    readonly property color textColor: "#7793a1"
    
    // Состояния
    property bool isActive: false
    property string activationKey: ""
    property string statusText: ""
    property bool showSuccess: false
    
    Component.onCompleted: {
        // Проверяем активацию при загрузке
        checkActivation()
    }
    
    // Проверка активации
    function checkActivation() {
        // Здесь будет вызов к Backend
        // backend.isProgramActivated()
    }
    
    // Активация ключом
    function activateWithKey(key) {
        statusText = "Проверка ключа..."
        // backend.activateWithKey(key)
    }
    
    Rectangle {
        anchors.fill: parent
        color: bgColor
        
        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(parent.width * 0.8, 500)
            spacing: 20
            
            // Логотип / Иконка
            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 100
                height: 100
                radius: 50
                color: "transparent"
                border.color: accentColor
                border.width: 3
                
                Text {
                    anchors.centerIn: parent
                    text: "🔑"
                    font.pixelSize: 50
                }
            }
            
            // Заголовок
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Активация программы"
                font.pixelSize: 24
                font.bold: true
                color: textColor
            }
            
            // Описание
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Для работы программы необходима активация.\nВведите ключ активации из Telegram."
                font.pixelSize: 14
                color: textColor
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            
            // Поле ввода ключа
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                color: cardColor
                radius: 8
                border.color: activationKey.length > 0 ? accentColor : "#333"
                border.width: 2
                
                TextInput {
                    id: keyInput
                    anchors.fill: parent
                    anchors.margins: 15
                    color: textColor
                    font.pixelSize: 16
                    font.family: "Courier New"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    placeholderText: "Введите ключ активации"
                    placeholderTextColor: "#555"
                    onTextChanged: activationKey = text
                    
                    Keys.onPressed: event => {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            activateButton.clicked()
                        }
                    }
                }
            }
            
            // Кнопка активации
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                radius: 8
                color: activationKey.length > 0 ? accentColor : "#333"
                
                Text {
                    anchors.centerIn: parent
                    text: "Активировать"
                    font.pixelSize: 16
                    font.bold: true
                    color: "white"
                }
                
                MouseArea {
                    anchors.fill: parent
                    enabled: activationKey.length > 0
                    onClicked: {
                        activateWithKey(keyInput.text)
                    }
                }
            }
            
            // Статус
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: statusText
                font.pixelSize: 14
                color: showSuccess ? "#4caf50" : "#f44336"
                visible: statusText.length > 0
            }
            
            // Разделитель
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: "#333"
            }
            
            // Кнопка купить подписку
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 45
                radius: 8
                color: "transparent"
                border.color: accentColor
                border.width: 2
                
                Text {
                    anchors.centerIn: parent
                    text: "💳 Купить подписку"
                    font.pixelSize: 14
                    font.bold: true
                    color: accentColor
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        Qt.openUrlExternally("https://web.tribute.tg/e/GY")
                    }
                }
            }
            
            // Кнопка поддержка
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 45
                radius: 8
                color: "transparent"
                border.color: "#333"
                border.width: 2
                
                Text {
                    anchors.centerIn: parent
                    text: "📞 Поддержка"
                    font.pixelSize: 14
                    font.bold: true
                    color: textColor
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        Qt.openUrlExternally("https://t.me/rtmnklvch")
                    }
                }
            }
        }
    }
}
