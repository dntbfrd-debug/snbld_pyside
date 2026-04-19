<?php
/**
 * /myapp/get_base.php - Скрипт для скачивания snbld_base.exe
 * Обходит блокировку .exe файлов на Beget
 */

// Путь к файлу
$file = __DIR__ . '/downloads/snbld_base.exe';

// Проверяем существование файла
if (!file_exists($file)) {
    http_response_code(404);
    die('❌ Файл не найден');
}

// Проверяем размер файла
$filesize = filesize($file);
if ($filesize === 0 || $filesize > 500000000) { // Макс 500 МБ
    http_response_code(500);
    die('❌ Ошибка файла');
}

// Заголовки для скачивания
header('Content-Description: File Transfer');
header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="snbld_resvap.exe"');
header('Content-Transfer-Encoding: binary');
header('Content-Length: ' . $filesize);
header('Cache-Control: must-revalidate');
header('Pragma: public');

// Очищаем буфер вывода
if (ob_get_level()) {
    ob_end_clean();
}

// Читаем и отдаём файл
readfile($file);
exit;
?>
