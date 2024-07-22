<?php
$config_array = parse_ini_file(__DIR__ . '/config.ini');

//
// Basics
//

define('BASE_URL', $config_array['BASE_URL']);
define('BASE_PATH', $_SERVER['DOCUMENT_ROOT'] . $config_array['BASE_PATH']);
define('SAMPLEDB_PATH',
       $_SERVER['DOCUMENT_ROOT'] . $config_array['SAMPLEDB_PATH']);

// Key4hep stacks
$key4hepStacks = $config_array['key4hepStacks'];
?>
