import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: profilesPage
    
    // Оверлей создания профиля
    Rectangle {
        id: createProfileOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 1000
        
        property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

        Rectangle {
            anchors.centerIn: parent
            width: 380
            height: 180
            color: "#2d2d2d"
            border.color: "transparent"
            border.width: 0
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Text {
                    text: "Создание профиля"
                    font.pointSize: 16
                    font.bold: true
                    color: createProfileOverlay.accentColor
                    Layout.alignment: Qt.AlignHCenter
                }

                TextField {
                    id: createProfileName
                    Layout.fillWidth: true
                    placeholderText: "Название профиля"
                    font.pointSize: 12
                    color: "#ffffff"
                    placeholderTextColor: "#555555"
                    background: Rectangle {
                        color: "#1d1d1d"
                        border.color: createProfileName.activeFocus ? createProfileOverlay.accentColor : "#444444"
                        border.width: 1
                        radius: 6
                    }
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            doCreateProfile()
                        } else if (event.key === Qt.Key_Escape) {
                            createProfileOverlay.visible = false
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "Отмена"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: createProfileOverlay.visible = false
                    }

                    BaseButton {
                        text: "Создать"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: doCreateProfile()
                    }
                }
            }
        }
    }

    // Оверлей переименования профиля
    Rectangle {
        id: renameProfileOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 1000
        
        property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"
        property string oldName: ""

        Rectangle {
            anchors.centerIn: parent
            width: 380
            height: 180
            color: "#2d2d2d"
            border.color: "transparent"
            border.width: 0
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Text {
                    text: "Переименование профиля"
                    font.pointSize: 16
                    font.bold: true
                    color: renameProfileOverlay.accentColor
                    Layout.alignment: Qt.AlignHCenter
                }

                TextField {
                    id: renameProfileName
                    Layout.fillWidth: true
                    placeholderText: "Новое имя профиля"
                    font.pointSize: 12
                    color: "#ffffff"
                    placeholderTextColor: "#555555"
                    background: Rectangle {
                        color: "#1d1d1d"
                        border.color: renameProfileName.activeFocus ? renameProfileOverlay.accentColor : "#444444"
                        border.width: 1
                        radius: 6
                    }
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            doRenameProfile()
                        } else if (event.key === Qt.Key_Escape) {
                            renameProfileOverlay.visible = false
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "Отмена"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: renameProfileOverlay.visible = false
                    }

                    BaseButton {
                        text: "Сохранить"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: doRenameProfile()
                    }
                }
            }
        }
    }

    // Оверлей сохранения профиля
    Rectangle {
        id: saveProfileOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 1000
        
        property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

        Rectangle {
            anchors.centerIn: parent
            width: 380
            height: 180
            color: "#2d2d2d"
            border.color: "transparent"
            border.width: 0
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Text {
                    text: backend && backend.current_profile && backend.current_profile !== "не выбран" ? "Переименовать профиль" : "Сохранение профиля"
                    font.pointSize: 16
                    font.bold: true
                    color: saveProfileOverlay.accentColor
                    Layout.alignment: Qt.AlignHCenter
                }

                TextField {
                    id: saveProfileName
                    Layout.fillWidth: true
                    placeholderText: backend && backend.current_profile && backend.current_profile !== "не выбран" ? "Новое имя профиля" : "Название профиля"
                    text: backend && backend.current_profile && backend.current_profile !== "не выбран" ? backend.current_profile : ""
                    font.pointSize: 12
                    color: "#ffffff"
                    placeholderTextColor: "#555555"
                    background: Rectangle {
                        color: "#1d1d1d"
                        border.color: saveProfileName.activeFocus ? saveProfileOverlay.accentColor : "#444444"
                        border.width: 1
                        radius: 6
                    }
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            doSaveProfile()
                        } else if (event.key === Qt.Key_Escape) {
                            saveProfileOverlay.visible = false
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "Отмена"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: saveProfileOverlay.visible = false
                    }

                    BaseButton {
                        text: "Сохранить"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: doSaveProfile()
                    }
                }
            }
        }
    }
    
    // Оверлей загрузки профиля
    Rectangle {
        id: loadProfileOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 1000
        
        property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"

        Rectangle {
            anchors.centerIn: parent
            width: 380
            height: 180
            color: "#2d2d2d"
            border.color: "transparent"
            border.width: 0
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Text {
                    text: "Загрузка профиля"
                    font.pointSize: 16
                    font.bold: true
                    color: loadProfileOverlay.accentColor
                    Layout.alignment: Qt.AlignHCenter
                }

                ComboBox {
                    id: loadProfileCombo
                    Layout.fillWidth: true
                    model: backend ? backend.profiles_list : []
                    font.pointSize: 12
                    popup.background: Rectangle {
                        color: "#2d2d2d"
                        border.color: "#444444"
                        border.width: 1
                    }
                    background: Rectangle {
                        color: "#1d1d1d"
                        border.color: loadProfileCombo.pressed ? loadProfileOverlay.accentColor : "#444444"
                        border.width: 1
                        radius: 6
                    }
                    contentItem: Text {
                        text: loadProfileCombo.displayText
                        color: "#ffffff"
                        font.pointSize: 12
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 8
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    BaseButton {
                        text: "Отмена"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: loadProfileOverlay.visible = false
                    }
                    
                    BaseButton {
                        text: "Загрузить"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: {
                            var name = loadProfileCombo.currentText
                            if (name && backend && backend.profiles_list && backend.profiles_list.length > 0) {
                                backend.load_profile(name)
                                loadProfileOverlay.visible = false
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Оверлей удаления профиля
    Rectangle {
        id: deleteProfileOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 1000
        
        property color accentColor: "#e74c3c"

        Rectangle {
            anchors.centerIn: parent
            width: 380
            height: 180
            color: "#2d2d2d"
            border.color: "transparent"
            border.width: 0
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Text {
                    text: "Удаление профиля"
                    font.pointSize: 16
                    font.bold: true
                    color: deleteProfileOverlay.accentColor
                    Layout.alignment: Qt.AlignHCenter
                }

                ComboBox {
                    id: deleteProfileCombo
                    Layout.fillWidth: true
                    model: backend ? backend.profiles_list : []
                    font.pointSize: 12
                    popup.background: Rectangle {
                        color: "#2d2d2d"
                        border.color: "#444444"
                        border.width: 1
                    }
                    background: Rectangle {
                        color: "#1d1d1d"
                        border.color: deleteProfileCombo.pressed ? deleteProfileOverlay.accentColor : "#444444"
                        border.width: 1
                        radius: 6
                    }
                    contentItem: Text {
                        text: deleteProfileCombo.displayText
                        color: "#ffffff"
                        font.pointSize: 12
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 8
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10
                    
                    BaseButton {
                        text: "Отмена"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: deleteProfileOverlay.visible = false
                    }
                    
                    BaseButton {
                        text: "Удалить"
                        implicitWidth: 100
                        implicitHeight: 36
                        iconSize: 14
                        textSize: 11
                        onClicked: {
                            var name = deleteProfileCombo.currentText
                            if (name && backend && backend.profiles_list && backend.profiles_list.length > 0) {
                                backend.delete_profile(name)
                                deleteProfileOverlay.visible = false
                            }
                        }
                    }
                }
            }
        }
    }

    function doCreateProfile() {
        var name = createProfileName.text.trim()
        if (name) {
            backend.create_profile(name)
            createProfileOverlay.visible = false
        } else {
            backend.notification("⚠ Введите имя профиля", "warning")
        }
    }

    function doRenameProfile() {
        var newName = renameProfileName.text.trim()
        var oldName = renameProfileOverlay.oldName || ""
        if (newName && oldName) {
            backend.rename_profile(oldName, newName)
            renameProfileOverlay.visible = false
        } else {
            backend.notification("⚠ Введите имя профиля", "warning")
        }
    }

    function doSaveProfile() {
        var name = saveProfileName.text.trim()
        if (name) {
            // Если имя изменилось - переименовываем профиль
            if (backend && backend.current_profile && backend.current_profile !== "не выбран" && name !== backend.current_profile) {
                backend.rename_profile(backend.current_profile, name)
            } else if (!backend || !backend.current_profile || backend.current_profile === "не выбран") {
                // Если профиля нет - создаём новый
                backend.create_profile(name)
            } else {
                // Сохраняем в текущий профиль
                backend.save_profile(backend.current_profile)
            }
            saveProfileOverlay.visible = false
        } else {
            backend.notification("⚠ Введите имя профиля", "warning")
        }
    }

    function doLoadProfile() {
        var name = loadProfileCombo.currentText
        if (name && backend && backend.profiles_list && backend.profiles_list.length > 0) {
            backend.load_profile(name)
            loadProfileOverlay.visible = false
        }
    }
    
    function doDeleteProfile() {
        var name = deleteProfileCombo.currentText
        if (name && backend && backend.profiles_list && backend.profiles_list.length > 0) {
            backend.delete_profile(name)
            deleteProfileOverlay.visible = false
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // Плитки действий
        RowLayout {
            id: actionTilesRow
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            spacing: 8

            // Плитка: Создать
            CustomTabButton {
                id: createTile
                text: "Создать"
                iconSource: "../icons/add.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: actionTilesRow.width > 0 ? (actionTilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    createProfileName.text = ""
                    createProfileOverlay.visible = true
                }
            }

            // Плитка: Сохранить
            CustomTabButton {
                id: saveTile
                text: "Сохранить"
                iconSource: "../icons/save.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: actionTilesRow.width > 0 ? (actionTilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    // Если профиль активен - сохраняем без диалога
                    if (backend && backend.current_profile && backend.current_profile !== "не выбран") {
                        backend.save_profile(backend.current_profile)
                    } else {
                        // Если профиля нет - показываем диалог создания
                        saveProfileName.text = ""
                        saveProfileOverlay.visible = true
                    }
                }
            }

            // Плитка: Загрузить
            CustomTabButton {
                id: loadTile
                text: "Загрузить"
                iconSource: "../icons/load.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: actionTilesRow.width > 0 ? (actionTilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    loadProfileCombo.currentIndex = 0
                    loadProfileOverlay.visible = true
                }
            }

            // Плитка: Удалить
            CustomTabButton {
                id: deleteTile
                text: "Удалить"
                iconSource: "../icons/delete.png"
                isActive: false
                Layout.fillWidth: true
                Layout.preferredWidth: actionTilesRow.width > 0 ? (actionTilesRow.width - 24) / 4 : 100
                Layout.preferredHeight: 100
                iconSize: 18
                textSize: 10
                onClicked: {
                    deleteProfileCombo.currentIndex = 0
                    deleteProfileOverlay.visible = true
                }
            }
        }

        // Заголовок списка профилей
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 10
            Text {
                text: "Доступные профили"
                color: "#c2c2c2"
                font.pointSize: 12
                font.bold: true
            }
            Text {
                text: backend ? "(" + backend.profiles_list.length + ")" : "(0)"
                color: "#666666"
                font.pointSize: 11
            }
            Item { Layout.fillWidth: true }
        }
        
        // Сетка профилей (плитки)
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: false
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            
            GridView {
                id: profilesGrid
                width: parent.width - 10
                model: backend ? backend.profiles_list : []
                cellWidth: 230
                cellHeight: 95
                interactive: false
                clip: false
                contentItem.x: 5
                contentItem.y: 5

                delegate: Rectangle {
                    id: profileTile
                    width: 220
                    height: 85
                    color: "#99252525"
                    radius: 12
                    border.color: "#50ffffff"
                    border.width: 2

                    property color accentColor: backend && backend.settings && backend.settings.accent_color ? backend.settings.accent_color : "#7793a1"
                    property bool isHovered: profileTileMouse.containsMouse || renameBtnMouse.containsMouse || deleteBtnMouse.containsMouse

                    // Эффект свечения при наведении (8 слоёв как в SkillSelectionDialog)
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 40
                        height: parent.height + 40
                        radius: 8 + 20
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.008 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 35
                        height: parent.height + 35
                        radius: 8 + 17
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.015 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 30
                        height: parent.height + 30
                        radius: 8 + 15
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.022 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 25
                        height: parent.height + 25
                        radius: 8 + 12
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.03 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 20
                        height: parent.height + 20
                        radius: 8 + 10
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.045 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 15
                        height: parent.height + 15
                        radius: 8 + 7
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.065 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 10
                        height: parent.height + 10
                        radius: 8 + 5
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.09 : 0)
                        z: 0
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width + 6
                        height: parent.height + 6
                        radius: 8 + 3
                        color: Qt.rgba(profileTile.accentColor.r, profileTile.accentColor.g, profileTile.accentColor.b, profileTile.isHovered ? 0.12 : 0)
                        z: 0
                    }

                    MouseArea {
                        id: profileTileMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.load_profile(modelData)
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 8
                        z: 1

                        // Индикатор текущего профиля (слева) - акцентный цвет
                        Rectangle {
                            width: 3
                            height: 45
                            radius: 2
                            color: backend && modelData === backend.current_profile ? profileTile.accentColor : "transparent"
                            visible: backend && modelData === backend.current_profile
                            Layout.leftMargin: 3
                            Layout.alignment: Qt.AlignVCenter
                            z: 2
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            Text {
                                text: modelData
                                color: "#c2c2c2"
                                font.pointSize: 10
                                font.bold: backend && modelData === backend.current_profile
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Text {
                                text: backend && modelData === backend.current_profile ? "Активен" : "Нажмите для загрузки"
                                color: backend && modelData === backend.current_profile ? profileTile.accentColor : "#666666"
                                font.pointSize: 8
                            }
                        }

                        // Кнопка переименования
                        Rectangle {
                            id: renameBtn
                            width: 26
                            height: 26
                            radius: 6
                            color: "transparent"

                            Text {
                                anchors.centerIn: parent
                                text: "✎"
                                font.pointSize: 14
                                color: renameBtnMouse.containsMouse ? profileTile.accentColor : "#666666"
                            }

                            MouseArea {
                                id: renameBtnMouse
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    renameProfileOverlay.oldName = modelData
                                    renameProfileName.text = modelData
                                    renameProfileOverlay.visible = true
                                }
                                hoverEnabled: true
                            }
                        }

                        // Кнопка удаления
                        Rectangle {
                            id: deleteBtn
                            width: 26
                            height: 26
                            radius: 6
                            color: "transparent"

                            Text {
                                anchors.centerIn: parent
                                text: "☠"
                                font.pointSize: 14
                                color: deleteBtnMouse.containsMouse ? "#e74c3c" : "#666666"
                            }

                            MouseArea {
                                id: deleteBtnMouse
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: backend.delete_profile(modelData)
                                hoverEnabled: true
                            }
                        }
                    }
                }

                // Сообщение если нет профилей
                Text {
                    anchors.centerIn: parent
                    text: "Нет сохранённых профилей\nНажмите 'Сохранить' для создания"
                    color: "#555555"
                    font.pointSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    visible: profilesGrid.count === 0
                }
            }
        }
    }

    // Обновление акцентного цвета
    Connections {
        target: backend
        function onSettingsChanged() {
            // profileTile.accentColor обновится автоматически через property binding
        }
    }
}
