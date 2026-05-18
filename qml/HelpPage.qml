import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15
import "components"

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
                text: "Помощь"
                font.pointSize: 20
                font.bold: true
                color: "#ef4444"
            }
            Item { Layout.fillWidth: true }
        }

        // ==================== БЫСТРЫЙ СТАРТ ====================
        GlassBlurPanel {
            id: quickStartBlock
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 260
            Layout.topMargin: 10
            border.color: "#ef4444"
            border.width: 2

            ColumnLayout {
                id: quickStartLayout
                anchors.fill: parent
                anchors.margins: 12
                spacing: 6

                Text {
                    text: "Быстрый старт — Создание скилл-макроса"
                    color: "#ef4444"
                    font.pointSize: 13
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
                    spacing: 16

                    // ЛЕВАЯ КОЛОНКА — Шаги 1-3
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: "Шаг 1: Привяжите окно игры"
                            color: "#ef4444"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "Откройте «Настройки → Окно». Нажмите «Выбрать окно» и кликните мышкой на окно вашей игры Perfect World. Это нужно чтобы программа «знала» куда отправлять нажатия клавиш."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 2: Настройте ресвап"
                            color: "#ef4444"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "В «Настройки → Ресвап» укажите клавиши смены сетов  (ПА сет, Пение сет). Также задайте процент максимального пения, при котором будет происходить смена сета."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 3: Настройте OCR"
                            color: "#ef4444"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "Откройте «Настройки → OCR ». Начните калибровку,с помощью мыши выделите зону, где отображаются цифры дистанции до цели. Также включите «Проверку дистанции» в настройках «Движение»."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    // ПРАВАЯ КОЛОНКА — Шаги 4-6
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: "Шаг 4: Откалибруйте кастбар"
                            color: "#ef4444"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "В «Настройки → OCR» нажмите на плитку  «Детекция каста».Начните калибровку,кликните мышкой на полоску прогресса каста в интерфейсе игры — это нужно для определения момента завершения каста."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 5: Создайте макрос"
                            color: "#ef4444"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "Перейдите в «Макросы» → «Создание». Выберите тип «Скиллы», укажите класс персонажа и нужный скилл. Назначьте клавишу или область активации. Создайте макрос."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Шаг 6: Запустите!"
                            color: "#ef4444"
                            font.pointSize: 10
                            font.bold: true
                        }
                        Text {
                            text: "Нажмите «-» (минус) для старта всех макросов, «=» (равно) для остановки. Также можно использовать кнопки «Старт/Стоп» в интерфейсе программы."
                            color: "#c2c2c2"
                            font.pointSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        // ==================== ОТКРЫТЫЙ КОД + ОБРАТНАЯ СВЯЗЬ ====================
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 110
            Layout.topMargin: 10
            spacing: 12

            // ЛЕВАЯ — Открытый код
                GlassBlurPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    border.color: "#50ffffff"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 3

                        Text {
                            text: "Обратная связь"
                            color: helpPage.accentColor
                            font.pointSize: 10
                            font.bold: true
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#40ffffff"
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Text {
                                text: "Telegram:"
                                color: "#a0a0a0"
                                font.pointSize: 8
                            }

                            Text {
                                text: "@rtmnklvch"
                                color: helpPage.accentColor
                                font.pointSize: 8
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
                            spacing: 6

                            Text {
                                text: "Сайт:"
                                color: "#a0a0a0"
                                font.pointSize: 8
                            }

                            Text {
                                text: "snbld.ru"
                                color: helpPage.accentColor
                                font.pointSize: 8
                                font.bold: true
                                font.underline: true

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: Qt.openUrlExternally("https://snbld.ru/site")
                                }
                            }
                        }

                        Item { Layout.fillHeight: true }
                }
            }
        }

        // ==================== ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ + ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ ====================
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 110
            Layout.topMargin: 10
            spacing: 12

            // ЛЕВАЯ — Пользовательское соглашение
            GlassBlurPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                border.color: "#50ffffff"
                border.width: 2

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 3

                    Text {
                        text: "Пользовательское соглашение"
                        color: helpPage.accentColor
                        font.pointSize: 10
                        font.bold: true
                    }

                    Rectangle {
                        width: parent.width
                        height: 1
                        color: "#40ffffff"
                    }

                    Text {
                        text: "Программа предоставляется «как есть». Используя snbld resvap, вы подтверждаете что понимаете риски использования автоматизированного ПО в онлайн играх. Разработчик не несет ответственности за возможные блокировки аккаунтов."
                        color: "#c2c2c2"
                        font.pointSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Text {
                        text: "Пользовательское соглашение"
                        color: helpPage.accentColor
                        font.pointSize: 8
                        font.bold: true
                        font.underline: true

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://snbld.ru/terms_site.html")
                        }
                    }
                }
            }

            // ПРАВАЯ — Политика конфиденциальности
            GlassBlurPanel {
                Layout.fillWidth: true
                Layout.fillHeight: true
                border.color: "#50ffffff"
                border.width: 2

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 3

                    Text {
                        text: "Политика конфиденциальности"
                        color: helpPage.accentColor
                        font.pointSize: 10
                        font.bold: true
                    }

                    Rectangle {
                        width: parent.width
                        height: 1
                        color: "#40ffffff"
                    }

                    Text {
                        text: "Программа собирает минимальные технические данные (HWID) для защиты лицензии и предотвращения несанкционированного доступа."
                        color: "#c2c2c2"
                        font.pointSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Text {
                        text: "Политика конфиденциальности"
                        color: helpPage.accentColor
                        font.pointSize: 8
                        font.bold: true
                        font.underline: true

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("https://snbld.ru/privacy_site.html")
                        }
                    }
                }
            }
        }
    }
}