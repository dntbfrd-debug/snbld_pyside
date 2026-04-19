import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: helpPage

    property string accentColor: backend && backend.settings ? backend.settings.accent_color : "#7793a1"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 0

        // Заголовок
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            spacing: 0

            Text {
                text: "◈ Помощь"
                font.pointSize: 20
                font.bold: true
                color: "#ef4444"
            }
            Item { Layout.fillWidth: true }
        }

        // ==================== БЫСТРЫЙ СТАРТ ====================
        Rectangle {
            id: quickStartBlock
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 280
            Layout.topMargin: 10
            color: "#99252525"
            radius: 10
            border.color: "#ef4444"
            border.width: 2

            ColumnLayout {
                id: quickStartLayout
                anchors.fill: parent
                anchors.margins: 14
                spacing: 8

                Text {
                    text: "🚀 Быстрый старт — Создание скилл-макроса"
                    color: "#ef4444"
                    font.pointSize: 14
                    font.bold: true
                }

                Rectangle {
                    width: parent.width
                    height: 1
                    color: "#40ffffff"
                }

                // 2 КОЛОНКИ ПО 3 ШАГА
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 20

                    // ЛЕВАЯ КОЛОНКА — Шаги 1-3
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            text: "Шаг 1: Привяжите окно игры"
                            color: "#ef4444"
                            font.pointSize: 11
                            font.bold: true
                        }
                        Text {
                            text: "Откройте «Настройки → Окно». Нажмите «Выбрать окно» и кликните мышкой на окно вашей игры Perfect World. Это нужно чтобы программа «знала» куда отправлять нажатия клавиш."
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 2: Настройте ресвап"
                            color: "#ef4444"
                            font.pointSize: 11
                            font.bold: true
                        }
                        Text {
                            text: "В «Настройки → Ресвап» укажите клавиши смены сетов оружия (ПА сет, Пение сет). Также задайте процент пения, при котором будет происходить смена сета."
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 3: Настройте OCR"
                            color: "#ef4444"
                            font.pointSize: 11
                            font.bold: true
                        }
                        Text {
                            text: "Откройте «Настройки → OCR области». С помощью мыши выделите зону, где отображаются цифры дистанции до цели. Также включите «Проверку дистанции» в настройках «Движение»."
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    // ПРАВАЯ КОЛОНКА — Шаги 4-6
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            text: "Шаг 4: Откалибруйте кастбар"
                            color: "#ef4444"
                            font.pointSize: 11
                            font.bold: true
                        }
                        Text {
                            text: "В «Настройки → Кастбар» нажмите «Начать калибровку». Кликните мышкой на полоску прогресса каста в интерфейсе игры — это нужно для определения момента завершения каста."
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 5: Создайте макрос"
                            color: "#ef4444"
                            font.pointSize: 11
                            font.bold: true
                        }
                        Text {
                            text: "Перейдите в «Макросы» → «Создание». Выберите тип «Скиллы», укажите класс персонажа и нужный скилл. Назначьте клавишу активации. Включите проверки: КД, дистанция, каст."
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 6: Запустите!"
                            color: "#ef4444"
                            font.pointSize: 11
                            font.bold: true
                        }
                        Text {
                            text: "Нажмите «-» (минус) для старта всех макросов, «=» (равно) для остановки. Также можно использовать кнопки «Старт/Стоп» в интерфейсе программы."
                            color: "#c2c2c2"
                            font.pointSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }

                // Советы
                Rectangle {
                    width: parent.width
                    height: 1
                    color: "#40ffffff"
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 20

                    Text {
                        text: "💡 «По клавише» — макрос активируется при нажатии горячей клавиши"
                        color: "#c2c2c2"
                        font.pointSize: 10
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Text {
                        text: "💡 «По области» — макрос срабатывает когда курсор мыши находится в заданной зоне экрана"
                        color: "#c2c2c2"
                        font.pointSize: 10
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        // ==================== ОТКРЫТЫЙ КОД + ОБРАТНАЯ СВЯЗЬ ====================
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 130
            Layout.topMargin: 12
            spacing: 16

            // ЛЕВАЯ — Открытый код
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#99252525"
                radius: 10
                border.color: "#50ffffff"
                border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "🔓 Открытый код"
                            color: "#4CAF50"
                            font.pointSize: 11
                            font.bold: true
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#40ffffff"
                        }

                        Text {
                            text: "Код открыт на GitHub. Проверяйте на вирусы!"
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "github.com/dntbfrd-debug/snbld_pyside"
                            color: "#4CAF50"
                            font.pointSize: 9
                            font.bold: true
                            font.underline: true

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Qt.openUrlExternally("https://github.com/dntbfrd-debug/snbld_pyside")
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }

                // ПРАВАЯ — Обратная связь (рамка как у «Открытый код»: 2px #50ffffff)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#99252525"
                    radius: 10
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4

                        Text {
                            text: "📞 Обратная связь"
                            color: helpPage.accentColor
                            font.pointSize: 11
                            font.bold: true
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#40ffffff"
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: "Telegram:"
                                color: "#a0a0a0"
                                font.pointSize: 9
                            }

                            Text {
                                text: "@rtmnklvch"
                                color: helpPage.accentColor
                                font.pointSize: 9
                                font.bold: true
                                font.underline: true

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Qt.openUrlExternally("https://t.me/rtmnklvch")
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: "Сайт:"
                                color: "#a0a0a0"
                                font.pointSize: 9
                            }

                            Text {
                                text: "snbld.ru"
                                color: helpPage.accentColor
                                font.pointSize: 9
                                font.bold: true
                                font.underline: true

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Qt.openUrlExternally("https://snbld.ru/webapp")
                                }
                            }
                        }

                        Text {
                            text: "Баги, предложения, помощь"
                            color: "#707070"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
        }
    }
}
