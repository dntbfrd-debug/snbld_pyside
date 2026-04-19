<?php
/**
 * download.php - Скрипт для скачивания snbld_resvap
 * Обходит блокировку .exe файлов на Beget
 */

$file = 'snbld_resvap_v1.4.0_setup.exe';

// Проверяем существование файла
if (!file_exists($file)) {
    http_response_code(404);
    die('File not found');
}

// Проверяем размер файла
$filesize = filesize($file);
if ($filesize === 0 || $filesize > 500000000) {
    http_response_code(500);
    die('File error');
}

// Заголовки для скачивания
header('Content-Description: File Transfer');
header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="snbld_resvap_v1.4.0_setup.exe"');
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